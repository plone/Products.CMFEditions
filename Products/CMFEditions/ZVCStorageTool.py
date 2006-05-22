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
from Products.CMFEditions.interfaces.IStorage import IPurgeSupport
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
    """Zope Version Control Based Version Storage
    
    There exist two selector schemas:
    
    - the one that counts removed versions also
    - the one that counts non removed version only
    
    Intended Usage:
    
    For different use cases different numbering schemas are used:
    
    - When iterating over the history the removed versions (usually) 
      aren't of interest. Thus the next valid version may be accessed
      by incrementing the selector and vice versa.
    - When retrieving a version beeing able to access removed version
      or correctly spoken a substitute (pretending to be the removed 
      version) is important when reconstructing relations between 
      objects.
    """

    __implements__ = (
        IPurgeSupport,
        IStorage,
        SimpleItem.__implements__,
    )
        
    id = 'portal_historiesstorage'
    alternative_id = 'portal_zvcstorage'
    
    meta_type = 'CMFEditions Portal ZVC based Histories Storage Tool'
    
    # make exceptions available trough the tool
    StorageError = StorageError
    StorageRetrieveError = StorageRetrieveError
    
    # shadow storage contains ZVCs __vc_info__ for every non purged 
    # version
    _shadowStorage = None
    
    # the ZVC repository ("the" version storage)
    zvc_repo = None
    
    # XXX obsolete
    _history_id_mapping = None
    _history_id_purgeCounters = None
    
    security = ClassSecurityInfo()
    
    # -------------------------------------------------------------------
    # methods implementing IStorage
    # -------------------------------------------------------------------

    security.declarePrivate('isRegistered')
    def isRegistered(self, history_id):
        """See IStorage.
        """
        # try to get the history of the resource (fails if not under 
        # version control)
        if self._shadowStorage is None or history_id is None:
            return False
        return history_id in self._getShadowStorage()['full']
        
    security.declarePrivate('register')
    def register(self, history_id, object, referenced_data={}, metadata=None):
        """See IStorage.
        """
        # check if already registered
        if self.isRegistered(history_id):
            return
        
        # No ZVC info available
        shadowInfo = {"vc_info": None}
        zvc_method = self._getZVCRepo().applyVersionControl
        try:
            return self._applyOrCheckin(zvc_method, history_id, shadowInfo,
                                        object, referenced_data, metadata)
        except VersionControlError:
            raise StorageRegisterError(
                "Registering the object with history id '%s' failed. "
                "The underlying storage implementation reported an error."
                % history_id)
        
    security.declarePrivate('save')
    def save(self, history_id, object, referenced_data={}, metadata=None):
        """See IStorage.
        """
        # check if already registered
        if not self.isRegistered(history_id):
            raise StorageUnregisteredError(
                "Saving an unregistered object is not possible. "
                "Register the object with history id '%s' first. "
                % history_id)
        
        # ZVC info from the previous checkin (or apply version control)
        shadowInfo = self._getShadowInfo(history_id, selector=None, 
                                         countPurged=True)
        zvc_method = self._getZVCRepo().checkinResource
        try:
            return self._applyOrCheckin(zvc_method, history_id, shadowInfo,
                                        object, referenced_data, metadata)
        except VersionControlError:
            raise StorageSaveError(
                "Saving the object with history id '%s' failed. "
                "The underlying storage implementation reported an error."
                % history_id)

    security.declarePrivate('retrieve')
    def retrieve(self, history_id, selector=None, 
                 countPurged=True, substitute=True):
        """See ``IStorage`` and Comments in ``IPurgePolicy``
        """
        zvc_repo = self._getZVCRepo()
        zvc_histid = self._getZVCHistoryId(history_id, countPurged)
        zvc_selector = self._getZVCSelector(history_id, selector, countPurged)
        
        # retrieve the object
        try:
            zvc_obj = zvc_repo.getVersionOfResource(zvc_histid, zvc_selector)
        except VersionControlError:
            # we should never get here (as an exception is raised in 
            # ``_getZVCSelector``)
            raise StorageRetrieveError(
                "Retrieving of object with history id '%s' failed. "
                "Version '%s' does not exist. " % (history_id, selector))
        
        # retrieve metadata
        logEntry = self._retrieveZVCLogEntry(zvc_histid, zvc_selector)
        metadata = self._decodeZVCMessage(logEntry.message)
        
        # wrap object and referenced data
        object = zvc_obj.getWrappedObject()
        referenced_data = zvc_obj.getReferencedData()
        data = VersionData(object, referenced_data, metadata)
        
        # check retrieved a "removed object" and check for substitue
        if substitute and isinstance(data.object, Removed):
            # delegate retrieving to purge policy if one is available
            # if none is available just return "the removed object"
            policy = getToolByName(self, 'portal_purgepolicy', None)
            if policy is not None:
                data = policy.retrieveSubstitute(history_id, selector, 
                                                 default=data)
        return data

    security.declarePrivate('getHistory')
    def getHistory(self, history_id, countPurged=True, substitute=True):
        """See IStorage.
        """
        return LazyHistory(self, history_id, countPurged, substitute)

    security.declarePrivate('getModificationDate')
    def getModificationDate(self, history_id, selector=None, 
                            countPurged=True, substitute=True):
        """See IStorage.
        """
        vdata = self.retrieve(history_id, selector, countPurged, substitute)
        return vdata.object.object.modified()


    # -------------------------------------------------------------------
    # methods implementing IPurgeSupport
    # -------------------------------------------------------------------

    # XXX check permission: shall not be private?
    security.declarePrivate('purge')
    def purge(self, history_id, selector, comment="", metadata={}, 
              countPurged=True):
        """See ``IPurgeSupport``
        """
        zvc_repo = self._getZVCRepo()
        zvc_histid = self._getZVCHistoryId(history_id, countPurged)
        zvc_selector = self._getZVCSelector(history_id, selector, countPurged)
        
        # digging into ZVC internals:
        # Get a reference to the version stored in the ZVC history storage
        #
        # Implementation Note:
        #
        # ZVCs ``getVersionOfResource`` is quite more complex. But as we 
        # do not use labeling and branches it is not a problem to get the
        # version in the following simple way.
        history = zvc_repo.getVersionHistory(zvc_histid)
        version = history.getVersionById(zvc_selector)
        data = version._data
        
        if not isinstance(data.getWrappedObject(), Removed):
            # remove from shadow storage
            selector = self._getVersionPos(history_id, selector, countPurged)
            del self._getShadowStorage()['available'][history_id][selector]
            
            # prepare replacement for the deleted object and metadata
            metadata = {
                "app_metadata": metadata,
                "sys_metadata": self._prepareSysMetadata(comment),
            }
            removedInfo = Removed("purged", metadata)
            
            # digging into ZVC internals: remove the stored object
            version._data = ZVCAwareWrapper(removedInfo, None, metadata)
            
            # digging into ZVC internals: replace the message
            logEntry = self._retrieveZVCLogEntry(zvc_histid, zvc_selector)
            logEntry.message = self._encodeMetadata(metadata)



    # -------------------------------------------------------------------
    # private helper methods
    # -------------------------------------------------------------------

    def _getLength(self, history_id, countPurged=True):
        """Returns the Length of the History
        """
        if not self.isRegistered(history_id):
            return 0
        
        if countPurged:
            history = self._getShadowStorage()['full']
        else:
            history = self._getShadowStorage()['available']
        return len(history[history_id])

    def _getVersionId(self, history_id, selector, countPurged):
        """Returns the Version Id
        """
        if selector is None:
            selector = self._getLength(history_id, countPurged=True) - 1
        elif not countPurged:
            # selector is a position information
            shadow = self._getShadowStorage()
            selector = shadow['available'][history_id][selector]
        return int(selector)

    def _getVersionPos(self, history_id, selector, countPurged):
        """Returns the Position in the Version History
        """
        if selector is None:
            selector = self._getLength(history_id, countPurged=False) - 1
        elif countPurged:
            history = self._getShadowStorage()['available'][history_id]
            # search from newest to oldest
            # optimziation: search from newest to oldest, simulating rindex
            #               by reversing before and after, reverse is damn fast!
            history.reverse()
            try:
                selector = len(history) - 1 - history.index(selector)
            except ValueError:
                selector = None
            history.reverse()
        return selector

    def _applyOrCheckin(self, zvc_method, history_id, shadowInfo, 
                        object, referenced_data, metadata):
        """Just centralizing similar code.
        """
        # delegate the decision if and what to purge to the purge policy 
        # tool if one exists. If the call returns ``True`` do not save 
        # or register the current version.
        policy = getToolByName(self, 'portal_purgepolicy', None)
        if policy is not None:
            if not policy.beforeSaveHook(history_id, object, metadata):
                return self._getHistoriesLength(history_id, 
                                                countPurged=True) - 1
        
        # prepare the object for beeing saved with ZVC
        #
        # - Recall the ``__vc_info__`` from the most current version
        #   (selector=None).
        # - Wrap the object, the referenced data and metadata
        vc_info = self._getVcInfo(object, shadowInfo)
        zvc_obj = ZVCAwareWrapper(object, referenced_data, metadata, 
                                  vc_info)
        message = self._encodeMetadata(metadata)
        
        # call appropriate ZVC method
        zvc_method(zvc_obj, message)
        
        # save the ``__vc_info__`` attached by the zvc call from above
        shadowInfo = {
            "vc_info": deepCopy(zvc_obj.__vc_info__),
        }
        self._saveShadowInfo(history_id, shadowInfo)
        
        return self._getLength(history_id, countPurged=True) - 1

    def _getShadowStorage(self):
        """Returns the Storage for Stuff Needed by ZVC
        """
        if self._shadowStorage is None:
            self._shadowStorage = OOBTree()
            self._shadowStorage['full'] = OOBTree()      # all
            self._shadowStorage['available'] = OOBTree() # not removed
        return self._shadowStorage

    def _saveShadowInfo(self, history_id, shadowInfo):
        """Save ZVC information
        """
        shadowStorage = self._getShadowStorage()
        if history_id in shadowStorage['full']:
            fullHistory = shadowStorage['full'][history_id]
            fullHistory.append(shadowInfo)
            shadowStorage['full']._p_changed = 1
            fullIndex = len(fullHistory) - 1
            availableHistory = shadowStorage['available'][history_id]
            availableHistory.append(fullIndex)
            shadowStorage['available']._p_changed = 1
        else:
            # first version
            shadowStorage['full'][history_id] = [shadowInfo]
            shadowStorage['available'][history_id] = [0]

    def _getShadowInfo(self, history_id, selector=None, countPurged=True):
        """Returns ZVC related informations
        """
        # try to get the history of the resource (fails if not under 
        # version control)
        try:
            fullHistory = self._getShadowStorage()['full'][history_id]
        except KeyError:
            raise StorageUnregisteredError(
                "Saving or retrieving an unregistered object is not "
                "possible. Register the object with history id '%s' first. "
                % history_id)
        
        # differentiate between the two numbering schematas
        if countPurged:
            # an unspecified selector is aequivalent to the most current 
            # version
            if selector is None:
                selector = len(fullHistory) - 1
        else:
            available = self._getShadowStorage()['available'][history_id]
            if selector is None:
                selector = -1
            selector = available[selector]
            
        return fullHistory[selector]

    # -------------------------------------------------------------------

    def _getZVCRepo(self):
        """Returns the Zope Version Control Repository
        
        Instantiates one with the first call.
        """
        if self.zvc_repo is None:
            self.zvc_repo = ZopeRepository('repo', 'ZVC Storage')
        return self.zvc_repo

    def _getZVCHistoryId(self, history_id, countPurged):
        """Returns the ZVC history id
        """
        shadowInfo = self._getShadowInfo(history_id, None, countPurged)
        return shadowInfo["vc_info"].history_id

    def _getZVCSelector(self, history_id, selector, countPurged):
        """Converts the CMFEditions selector into a ZVC selector
        """
        try:
            selector = self._getVersionId(history_id, selector, countPurged)
        except IndexError:
            raise StorageRetrieveError(
                "Retrieving of object with history id '%s' failed. "
                "Version '%s' does not exist. " % (history_id, selector))
        
        # ZVC's first version is version 1 and is of type string
        return str(selector + 1)

    def _getVcInfo(self, obj, shadowInfo, set_checked_in=False):
        """Recalls ZVC Related Informations and Attaches them to the Object
        """
        vc_info = deepCopy(shadowInfo["vc_info"])
        if vc_info is None:
            return None
        
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
        obj.__vc_info__ = vc_info # getVersionIds needs it (XXX check)
        vc_info.version_id = str(len(zvc_repo.getVersionIds(obj)))
        return vc_info

    def _retrieveZVCLogEntry(self, zvc_histid, zvc_selector):
        """Retrieves the metadata from ZVCs log
        
        Unfortunately this may get costy with long histories.
        We should really store metadata in the shadow storage in the
        future or loop over the log in reverse.
        """
        zvc_repo = self._getZVCRepo()
        log = zvc_repo.getVersionHistory(zvc_histid).getLogEntries()
        checkin = LogEntry.ACTION_CHECKIN
        entries = [e for e in log if e.version_id==zvc_selector and e.action==checkin]
        
        # just make a log entry if something wrong happened
        if len(entries) != 1:
            zLOG.LOG("CMFEditions ASSERT:", zLOG.INFO,
                     "Uups, an object has been stored %s times with the same "
                     "history '%s'!!!" % (len(entry), zvc_selector))
        
        return entries[0]

    def _encodeMetadata(self, metadata):
        # metadata format is:
        #    - first line with trailing \x00: comment or empty comment
        #    - then: pickled metadata (incl. comment)
        try:
            comment = metadata['sys_metadata']['comment']
        except KeyError:
            comment = ''
        return '\x00\n'.join((comment, dumps(metadata, HIGHEST_PROTOCOL)))

    def _decodeZVCMessage(self, message):
        return loads(message.split('\x00\n', 1)[1])

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

InitializeClass(ZVCStorageTool)


class ZVCAwareWrapper(Persistent):
    """ZVC assumes the stored object has a getPhysicalPath method.
    
    ZVC, arghh ...
    """
    def __init__(self, object, referenced_data, metadata, vc_info=None):
        self._object = object
        self._referenced_data = referenced_data
        self._physicalPath = \
            metadata['sys_metadata'].get('physicalPath', ())[:] # copy
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

    def isValid(self):
        """Returns True if Valid (not Purged)
        """
        return not isinstance(self.object, Removed)

class LazyHistory:
    """Lazy history adapter.
    """
    
    __implements__ = (
        IHistory,
    )

    def __init__(self, storage, history_id, countPurged=True, substitute=True):
        """See IHistory.
        """
        self._history_id = history_id
        self._countPurged = countPurged
        self._substitute = substitute
        self._length = storage._getLength(history_id, countPurged)
        self._retrieve = storage.retrieve

    def __len__(self):
        """See IHistory.
        """
        return self._length

    def __getitem__(self, selector):
        """See IHistory.
        """
        return self._retrieve(self._history_id, selector, self._countPurged, 
                              self._substitute)

    def __iter__(self):
        """See IHistory.
        """
        return GetItemIterator(self.__getitem__,
                               stopExceptions=(StorageRetrieveError,))


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
        self._pos += 1
        try:
            return self._getItem(self._pos)
        except self._stopExceptions:
            raise StopIteration()
