#########################################################################
# Copyright (c) 2004, 2005 Alberto Berti, Gregoire Weber. 
# All Rights Reserved.
# 
# This file is part of CMFEditions.
# 
# CMFEditions is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# CMFEditions is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with CMFEditions; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#########################################################################
"""Histories Storage using ZVC

$Id: ZVCStorageTool.py,v 1.18 2005/03/11 11:05:12 varun-rastogi Exp $
"""
__version__ = "$Revision: 1.18 $"

import traceback
import sys
import time
from StringIO import StringIO
from cPickle import Pickler, Unpickler, dumps, loads, HIGHEST_PROTOCOL

import zLOG

from Globals import InitializeClass
from BTrees.OOBTree import OOBTree
from Persistence import Persistent
from AccessControl import ClassSecurityInfo, getSecurityManager

from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.interfaces import IOpaqueItems

from Products.ZopeVersionControl.ZopeRepository import ZopeRepository
from Products.ZopeVersionControl.Utility import VersionControlError
from Products.ZopeVersionControl.EventLog import LogEntry

from Products.CMFEditions.interfaces.IStorage import IStorage
from Products.CMFEditions.interfaces.IPurgeSupport import IPurgeSupport
from Products.CMFEditions.interfaces.IStorage import IHistory
from Products.CMFEditions.interfaces.IStorage import IVersionData
from Products.CMFEditions.interfaces.IStorage import StorageError
from Products.CMFEditions.interfaces.IStorage import StorageRegisterError
from Products.CMFEditions.interfaces.IStorage import StorageSaveError
from Products.CMFEditions.interfaces.IStorage import StorageRetrieveError
from Products.CMFEditions.interfaces.IStorage import StorageUnregisteredError
    

def deepCopy(obj):
    stream = StringIO()
    p = Pickler(stream, 1)
    p.dump(obj)
    stream.seek(0)
    u = Unpickler(stream)
    return u.load()


class ZVCStorageTool(UniqueObject, SimpleItem, ActionProviderBase):
    """
    """

    __implements__ = (
        SimpleItem.__implements__,
        IStorage,
        IPurgeSupport,
    )
        
    id = 'portal_historiesstorage'
    alternative_id = 'portal_zvcstorage'
    
    meta_type = 'CMFEditions Portal ZVC based Histories Storage Tool'
    
    # make exceptions available trough the tool
    StorageError = StorageError
    StorageRetrieveError = StorageRetrieveError
    
    
    _history_id_mapping = None
    _history_id_purgeCounters = None
    zvc_repo = None
    
    security = ClassSecurityInfo()
    
    # -------------------------------------------------------------------
    # private helper methods
    # -------------------------------------------------------------------

    def _getZVCRepo(self):
        if self.zvc_repo is None:
            self.zvc_repo = ZopeRepository('repo', 'ZVC Storage')
        return self.zvc_repo

    def _getHistoryIdMapping(self):
        if self._history_id_mapping is None:
            self._history_id_mapping = OOBTree()
        return self._history_id_mapping

    def _getHistoryIdPurgeCounters(self):
        if self._history_id_purgeCounters is None:
            self._history_id_purgeCounters = OOBTree()
        return self._history_id_purgeCounters

    def _incrementPurgeCount(self, history_id):
        purgeCounters = self._getHistoryIdPurgeCounters()
        purgeCounter = purgeCounters.get(history_id, 0)
        purgeCounters[history_id] = purgeCounter + 1

    def _getPurgeCount(self, history_id):
        return self._getHistoryIdPurgeCounters().get(history_id, 0)

    def _getVCInfo(self, history_id):
        """Returns the ZVC 'vc_info' object.
        """
        try:
            return self._getHistoryIdMapping()[history_id]
        except KeyError:
            raise StorageUnregisteredError(
                "Saving or retrieving an unregistered object is not "
                "possible. Register the object with history id '%s' first. "
                % history_id)
        
    def _saveZVCInfo(self, obj, history_id):
        """Saves ZVC related informations and deletes them from the object.
        """
        vc_info = deepCopy(obj.__vc_info__)
        self._getHistoryIdMapping()[history_id] = vc_info
    
    def _prepareZVCInfo(self, obj, history_id, set_checked_in=False):
        """Recalls ZVC related informations and attaches them to the object.
        """
        vc_info = deepCopy(self._getVCInfo(history_id))
        
        # fake sticky information (no branches)
        vc_info.sticky = None
        
        # On rollback operations the repository expects the object 
        # to be in CHECKED_IN state.
        if set_checked_in:
            vc_info.status = vc_info.CHECKED_IN
        else:
            vc_info.status = vc_info.CHECKED_OUT
            
        # fake the version to be able to save a retrieved version later
        zvc_repo = self._getZVCRepo()
        
        obj.__vc_info__ = vc_info # getVersionIds needs it
        vc_info.version_id = str(len(zvc_repo.getVersionIds(obj)))
        
        return vc_info
    
    def _retrieveLogEntry(self, zvc_histid, zvc_selector):
        """Retrieves the metadata from ZVCs log
        
        Unfortunately this may get costy with long histories.
        """
        zvcrepo = self._getZVCRepo()
        log = zvcrepo.getVersionHistory(zvc_histid).getLogEntries()
        checkin = LogEntry.ACTION_CHECKIN
        entries = [e for e in log if e.version_id==zvc_selector and e.action==checkin]
        
        # just make a log entry if something wrong happened
        if len(entries) != 1:
            zLOG.LOG("CMFEditions ASSERT:", zLOG.INFO,
                     "Uups, an object has been stored %s times with the same "
                     "history '%s'!!!" % (len(entry), zvc_selector))
        
        return entries[0]

    def _decodeZVCMessage(self, message):
        return loads(message.split('\x00\n', 1)[1])

    def _encodeMetadata(self, metadata):
        # metadata format is:
        #    - first line with traling \x00: comment or empty comment
        #    - then: pickled metadata (incl. comment)
        try:
            comment = metadata['sys_metadata']['comment']
        except KeyError:
            comment = ''
        return '\x00\n'.join((comment, dumps(metadata, HIGHEST_PROTOCOL)))

    def _getZVCHistoryId(self, history_id):
        """Returns the ZVC history id.
        """
        return self._getVCInfo(history_id).history_id
    
    def _getHistoriesLength(self, zvc_histid):
        """Returns the length of the history
        """
        zvcrepo = self._getZVCRepo()
        history = zvcrepo.getVersionHistory(zvc_histid)
        return len(history.getVersionIds())
    
    def _getZVCSelector(self, zvc_histid, selector):
        """Converts the CMFEditions selector into a ZVC selector
        """
        if selector is None:
            # None means HEAD, the selector for the head is the histories 
            # length (may change with branches)
            selector = self._getHistoriesLength(zvc_histid)
        else:
            # ZVC's first version is version 1 ("our" selector starts with 0)
            # the value passed possibly is a number in string format
            selector = int(selector) + 1
        
        # ZVC expects version selectors being string numbers
        return str(selector)
    
    def _retrieve(self, zvc_histid, selector=None):
        """Private method returning a version by the ZVC history_id.
        """
        zvc_selector = self._getZVCSelector(zvc_histid, selector)
        
        # retrieve the object
        zvcrepo = self._getZVCRepo()
        try:
            zvc_obj = zvcrepo.getVersionOfResource(zvc_histid, zvc_selector)
        except VersionControlError:
            raise StorageRetrieveError(
                "Retrieving of object with history id '%s' failed. "
                "Version '%s' does not exist. "
                % (zvc_histid, zvc_selector))
        
        # internal bookkeeping: just store ZVC info from the object
        self._saveZVCInfo(zvc_obj, zvc_histid)
        
        # retrieve metadata
        logEntry = self._retrieveLogEntry(zvc_histid, zvc_selector)
        metadata = self._decodeZVCMessage(logEntry.message)
        
        object = zvc_obj.getWrappedObject()
        referenced_data = zvc_obj.getReferencedData()
        return VersionData(object, referenced_data, metadata)

    def _applyOrCheckin(self, method_name, vc_info, history_id, 
                        object, referenced_data, metadata):
        """Just centralizing similar code.
        """
        zvc_repo = self._getZVCRepo()
        zvc_obj = ZVCAwareWrapper(object, referenced_data, metadata, vc_info)
        message = self._encodeMetadata(metadata)
        
        # call applyVersionControl or checkinResource (or any other)
        getattr(zvc_repo, method_name)(zvc_obj, message)
        
        self._saveZVCInfo(zvc_obj, history_id)
        zvc_histid = self._getZVCHistoryId(history_id)
        return self._getHistoriesLength(zvc_histid) - 1

    def _prepareSysMetadata(self, comment):
        return {
            # comment is system metadata
            'comment': comment,
            # setting a timestamp here set the same timestamp at all
            # recursively saved objects
            'timestamp': int(time.time()),
            # ZVC needs a physical path (may be root)
            'physicalPath': (),
        }


    # -------------------------------------------------------------------
    # methods implementing IStorage
    # -------------------------------------------------------------------

    security.declarePrivate('isRegistered')
    def isRegistered(self, history_id):
        """See IStorage.
        """
        if history_id is None:
            return False
        return self._getHistoryIdMapping().get(history_id, False)
        
    security.declarePrivate('register')
    def register(self, history_id, object, referenced_data={}, metadata=None):
        """See IStorage.
        """
        # check if already registered
        try:
            self._getZVCHistoryId(history_id)
        except StorageUnregisteredError:
            vc_info = None
        else:
            # already registered
            return
        
        try:
            return self._applyOrCheckin('applyVersionControl', None, history_id, 
                                        object, referenced_data, metadata)
        except VersionControlError:
            raise StorageRegisterError(
                "Registering the object with history id '%s' failed. "
                % history_id)
        
    security.declarePrivate('save')
    def save(self, history_id, object, referenced_data={}, metadata=None):
        """See IStorage.
        """
        vc_info = self._prepareZVCInfo(object, history_id)
        
        try:
            return self._applyOrCheckin('checkinResource', vc_info, history_id, 
                                        object, referenced_data, metadata)
        except VersionControlError:
            raise StorageSaveError(
                "Saving the object with history id '%s' failed." 
                % history_id)

    security.declarePrivate('retrieve')
    def retrieve(self, history_id, selector=None):
        """See IStorage.
        """
        zvc_histid = self._getZVCHistoryId(history_id)
        return self._retrieve(zvc_histid, selector)
    
    security.declarePrivate('getHistory')
    def getHistory(self, history_id):
        """See IStorage.
        """
        return LazyHistory(self, history_id)

    security.declarePrivate('getModificationDate')
    def getModificationDate(self, history_id, selector=None):
        """See IStorage.
        """
        vdata = self.retrieve(history_id, selector)
#        return vdata.object.object.ModificationDate()
        return vdata.object.object.modified()

    # -------------------------------------------------------------------
    # methods implementing IPurgeSupport
    # -------------------------------------------------------------------

    security.declarePrivate('purge') # XXX not private, by permission
    def purge(self, history_id, selector, comment="", metadata={}):
        """See ``IPurgeSupport``
        """
        zvcrepo = self._getZVCRepo()
        zvc_histid = self._getZVCHistoryId(history_id)
        zvc_selector = self._getZVCSelector(zvc_histid, selector)
        
        # Get a reference to the version stored in the ZVC history storage
        #
        # Implementation Note:
        #
        # ZVCs ``getVersionOfResource`` is quite more complex. But as we 
        # do not use labeling and branches it is not a problem to get the
        # version in the following simple way.
        history = zvcrepo.getVersionHistory(zvc_histid)
        version = history.getVersionById(zvc_selector)
        
        data = version._data
        if type(data.getWrappedObject()) is not Removed:
            # increment the purge count to be able to deliver the 
            # effective length of the history fast
            self._incrementPurgeCount(history_id)
            
            # prepare replacement for the deleted object and metadata
            metadata = {
                "app_metadata": metadata,
                "sys_metadata": self._prepareSysMetadata(comment),
            }
            removedInfo = Removed("purged", metadata)
            
            # digging into ZVC internals: remove the stored object
            version._data = ZVCAwareWrapper(removedInfo, None, metadata)
            
            # digging into ZVC internals: replace the message
            logEntry = self._retrieveLogEntry(zvc_histid, zvc_selector)
            logEntry.message = self._encodeMetadata(metadata)

    security.declarePrivate('retrieveUnsubstituted')
    def retrieveUnsubstituted(self, history_id, selector=None):
        """See ``IPurgeSupport``
        """
        zvc_histid = self._getZVCHistoryId(history_id)
        return self._retrieve(zvc_histid, selector)

    security.declarePrivate('getLength')
    def getLength(self, history_id, ignorePurged=True):
        """See ``IPurgeSupport``
        """
        zvc_histid = self._getZVCHistoryId(history_id)
        length = self._getHistoriesLength(zvc_histid)
        if ignorePurged:
            length -= self._getPurgeCount(history_id)
        return length


class ZVCAwareWrapper(Persistent):
    """ZVC assumes the stored object has a getPhysicalPath method.
    
    ZVC, arghh ...
    """
    def __init__(self, object, referenced_data, metadata, vc_info=None):
        self._object = object
        self._referenced_data = referenced_data
        # we like to have a copy of the tuple
        self._physicalPath = () + metadata['sys_metadata'].get('physicalPath', ())
        if vc_info is not None:
            self.__vc_info__ = vc_info
        
    def getWrappedObject(self):
        return self._object
        
    def getReferencedData(self):
        return self._referenced_data
        
    def getPhysicalPath(self):
        return self._physicalPath


class Removed(Persistent):
    """Indicates that removement of data
    """
    
    def __init__(self, reason, metadata):
        """Store Removed Info
        """
        self.reason = reason
        self.metadata = metadata


class VersionData:
    __implements__ = (IVersionData, )
    
    def __init__(self, object, referenced_data, metadata):
        self.object = object
        self.referenced_data = referenced_data
        self.metadata = metadata


class LazyHistory:
    """Lazy history adapter.
    """
    
    __implements__ = (
        IHistory,
    )

    def __init__(self, storage, history_id):
        self._storage = storage
        self._zvc_histid = self._storage._getZVCHistoryId(history_id)
    
    def __len__(self):
        return self._storage._getHistoriesLength(self._zvc_histid)

    def __getitem__(self, selector):
        # XXX check bug: ``selector`` is CMFEditions selector but has 
        #     to be a ZVC selector.
        return self._storage._retrieve(self._zvc_histid, selector)
        
    def __iter__(self):
        return GetItemIterator(self.__getitem__, StorageRetrieveError)

InitializeClass(ZVCStorageTool)


class GetItemIterator:
    """Iterator object using a getitem implementation to iterate over.
    """
    def __init__(self, getItem, stopExceptions):
        self._getItem = getItem
        self._stopExceptions = stopExceptions
        self._pos = -1

    def __iter__(self):
        return self
        
    def next(self):
        try:
            self._pos += 1
            return self._getItem(self._pos)
        except self._stopExceptions:
            raise StopIteration()
