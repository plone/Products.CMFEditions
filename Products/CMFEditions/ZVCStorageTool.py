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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.interfaces import IOpaqueItems
from Products.CMFCore.CMFCorePermissions import ManagePortal

from Products.ZopeVersionControl.ZopeRepository import ZopeRepository
from Products.ZopeVersionControl.Utility import VersionControlError
from Products.ZopeVersionControl.EventLog import LogEntry

from Products.CMFEditions.interfaces.IStorage import IStorage
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
    )
        
    id = 'portal_historiesstorage'
    alternative_id = 'portal_zvcstorage'
    
    meta_type = 'CMFEditions Portal ZVC based Histories Storage Tool'
    
    storageStatistics = PageTemplateFile('www/storageStatistics.pt',
                                         globals(),
                                         __name__='modifierEditForm')
    manage_options = ActionProviderBase.manage_options[:] \
                     + ({'label' : 'Statistics (may take time)', 'action' : 'storageStatistics'}, ) \
                     + SimpleItem.manage_options[:]

    # make exceptions available trough the tool
    StorageError = StorageError
    StorageRetrieveError = StorageRetrieveError
    
    _history_id_mapping = None
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
    
    def _prepareMetadata(self, metadata):
        # metadata format is:
        #    - first line: comment or empty comment
        #    - then: pickled metadata (incl. comment)
        try:
            comment = metadata['sys_metadata']['comment']
        except KeyError:
            comment = ''
        return '\x00\n'.join((comment, dumps(metadata, HIGHEST_PROTOCOL)))

    def _recallMetadata(self, message):
        # we know the comment is still there in the pickled metadata
        return loads(message.split('\x00\n', 1)[1])
    
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
    
    def _retrieve(self, zvc_histid, selector=None):
        """Private method returning a version by the ZVC history_id.
        """
        # ----- check selector
        if selector is None:
            # None means HEAD, the selector for the head is the histories 
            # length (may change with branches)
            selector = self._getHistoriesLength(zvc_histid)
        else:
            # ZVC's first version is version 1 ("our" selector starts with 0)
            # the value passed possibly is a number in string format
            selector = int(selector) + 1
        
        # ZVC expects version selectors being string numbers
        selector = str(selector)
        
        # ----- retrieve the object
        zvcrepo = self._getZVCRepo()
        try:
            zvc_obj = zvcrepo.getVersionOfResource(zvc_histid, selector)
        except VersionControlError:
            raise StorageRetrieveError(
                "Retrieving of object with history id '%s' failed. "
                "Version '%s' does not exist. "
                % (zvc_histid, selector))
        
        # just store ZVC info from the object
        self._saveZVCInfo(zvc_obj, zvc_histid)
        
        # ----- retrieve metadata
        # Get the right message from the ZVC log. Unfortunately this may get 
        # costly with long histories.
        # XXX has to be optimized somehow (by saving metadata separately?)
        log = zvcrepo.getVersionHistory(zvc_histid).getLogEntries()
        checkin = LogEntry.ACTION_CHECKIN
        entries = [e for e in log if e.version_id==selector and e.action==checkin]
        
        # just make a log entry if something wrong happened
        if len(entries) != 1:
            zLOG.LOG("CMFEditions ASSERT:", zLOG.INFO,
                     "Uups, an object has been stored %s times with the same "
                     "history '%s'!!!" % (len(entry), selector))
        
        object = zvc_obj.getWrappedObject()
        referenced_data = zvc_obj.getReferencedData()
        metadata = self._recallMetadata(entries[0].message)
        return VersionData(object, referenced_data, metadata)

    def _applyOrCheckin(self, method_name, vc_info, history_id, 
                        object, referenced_data, metadata):
        """Just centralizing similar code.
        """
        zvc_repo = self._getZVCRepo()
        zvc_obj = ZVCAwareWrapper(object, referenced_data, metadata, vc_info)
        metadata = self._prepareMetadata(metadata)
        
        # call applyVersionControl or checkinResource (or any other)
        getattr(zvc_repo, method_name)(zvc_obj, metadata)
        
        self._saveZVCInfo(zvc_obj, history_id)
        zvc_histid = self._getZVCHistoryId(history_id)
        return self._getHistoriesLength(zvc_histid) - 1


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
    # ZMI methods
    # -------------------------------------------------------------------

    security.declareProtected(ManagePortal, 'zmi_getStorageStatistics')
    def zmi_getStorageStatistics(self):
        """
        """
        startTime = time.time()
        # get all history ids (incl. such that were deleted in the portal)
        historyIds = self._getHistoryIdMapping()
        hidhandler = getToolByName(self, "portal_historyidhandler")
        portal_paths_len = len(getToolByName(self, "portal_url")())
        
        # collect interesting informations
        histories = []
        for hid in historyIds:
            history = self.getHistory(hid)
            length = len(history)
            workingCopy = hidhandler.queryObject(hid)
            if workingCopy is not None:
                path = workingCopy.absolute_url()[portal_paths_len:]
                portal_type = workingCopy.getPortalTypeName()
            else:
                path = None
                retrieved = self.retrieve(hid).object.object
                portal_type = retrieved.getPortalTypeName()
            histData = {"history_id": hid, "length": length, "path": path,
                        "portal_type": portal_type}
            histories.append(histData)
        
        # collect history ids with still existing working copies
        existing = []
        deleted = []
        for histData in histories:
            if histData["path"] is None:
                deleted.append(histData)
            else:
                existing.append(histData)
        
        processingTime = "%.2f" % round(time.time() - startTime, 2)
        return {
            "existing": existing, 
            "deleted": deleted, 
            "time": processingTime,
        }

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
