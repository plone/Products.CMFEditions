#########################################################################
# Copyright (c) 2004, 2005, 2006 Alberto Berti, Gregoire Weber.
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

"""
__version__ = "$Revision: 1.18 $"

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from io import BytesIO
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from pickle import dumps
from pickle import HIGHEST_PROTOCOL
from pickle import loads
from pickle import Pickler
from pickle import Unpickler
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import UniqueObject
from Products.CMFEditions.interfaces import IStorageTool
from Products.CMFEditions.interfaces.IStorage import IHistory
from Products.CMFEditions.interfaces.IStorage import IPurgeSupport
from Products.CMFEditions.interfaces.IStorage import IStorage
from Products.CMFEditions.interfaces.IStorage import IStreamableReference
from Products.CMFEditions.interfaces.IStorage import IVersionData
from Products.CMFEditions.interfaces.IStorage import StorageError
from Products.CMFEditions.interfaces.IStorage import StoragePurgeError
from Products.CMFEditions.interfaces.IStorage import StorageRegisterError
from Products.CMFEditions.interfaces.IStorage import StorageRetrieveError
from Products.CMFEditions.interfaces.IStorage import StorageSaveError
from Products.CMFEditions.interfaces.IStorage import StorageUnregisteredError
from Products.CMFEditions.Permissions import AccessPreviousVersions
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.ZopeVersionControl.EventLog import LogEntry
from Products.ZopeVersionControl.Utility import VersionControlError
from Products.ZopeVersionControl.ZopeRepository import ZopeRepository
from zope.interface import implementer

import logging
import time
import types


logger = logging.getLogger("CMFEditions")


def deepCopy(obj):
    stream = BytesIO()
    p = Pickler(stream, 1)
    p.dump(obj)
    stream.seek(0)
    u = Unpickler(stream)
    return u.load()


def getSize(obj):
    """Calculate the size as cheap as possible"""
    # Try the cheap variants first.
    # Actually the checks ensure the code never fails but beeing sure
    # is better.
    try:
        # check if to return zero (length is zero)
        if len(obj) == 0:
            return 0
    except:  # noqa E722
        pass

    try:
        # check if ``IStreamableReference``
        if IStreamableReference.providedBy(obj):
            size = obj.getSize()
            if size is not None:
                return size
    except:  # noqa E722
        pass

    try:
        # string
        if isinstance(obj, types.StringTypes):
            return len(obj)
    except:  # noqa E722
        pass

    try:
        # file like object
        methods = dir(obj)
        if "seek" in methods and "tell" in methods:
            currentPos = obj.tell()
            obj.seek(0, 2)
            size = obj.tell()
            obj.seek(currentPos)
            return size
    except:  # noqa E722
        pass

    try:
        # fallback: pickling the object
        stream = BytesIO()
        p = Pickler(stream, 1)
        p.dump(obj)
        size = stream.tell()
    except:  # noqa E722
        size = None

    return size


@implementer(
    IPurgeSupport,
    IStorage,
    IStorageTool,
)
class ZVCStorageTool(UniqueObject, SimpleItem):
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

    id = "portal_historiesstorage"
    alternative_id = "portal_zvcstorage"

    meta_type = "CMFEditions Portal ZVC based Histories Storage Tool"

    storageStatistics = PageTemplateFile(
        "www/storageStatistics.pt", globals(), __name__="modifierEditForm"
    )
    manage_options = (
        {"label": "Statistics (may take time)", "action": "storageStatistics"},
    ) + SimpleItem.manage_options[:]

    # make exceptions available trough the tool
    StorageError = StorageError
    StorageRetrieveError = StorageRetrieveError

    # shadow storage contains ZVCs __vc_info__ for every non purged
    # version
    _shadowStorage = None

    # the ZVC repository ("the" version storage)
    zvc_repo = None

    security = ClassSecurityInfo()

    # -------------------------------------------------------------------
    # methods implementing IStorage
    # -------------------------------------------------------------------

    security.declarePrivate("isRegistered")

    def isRegistered(self, history_id):
        """See IStorage."""
        # Do not wake up the ZODB (aka write to it) if there wasn't any
        # version saved yet.
        shadow_storage = self._getShadowStorage(autoAdd=False)
        if shadow_storage is None:
            return False
        return shadow_storage.isRegistered(history_id)

    security.declarePrivate("register")

    def register(self, history_id, object, referenced_data={}, metadata=None):
        """See IStorage."""
        # check if already registered
        if self.isRegistered(history_id):
            return

        # No ZVC info available at register time
        shadowInfo = {"vc_info": None}
        zvc_method = self._getZVCRepo().applyVersionControl
        try:
            return self._applyOrCheckin(
                zvc_method, history_id, shadowInfo, object, referenced_data, metadata
            )
        except VersionControlError:
            raise StorageRegisterError(
                "Registering the object with history id '%s' failed. "
                "The underlying storage implementation reported an error." % history_id
            )

    security.declarePrivate("save")

    def save(self, history_id, object, referenced_data={}, metadata=None):
        """See IStorage."""
        # check if already registered
        if not self.isRegistered(history_id):
            raise StorageUnregisteredError(
                "Saving an unregistered object is not possible. "
                "Register the object with history id '%s' first. " % history_id
            )

        # retrieve the ZVC info from the youngest version
        history = self._getShadowHistory(history_id, autoAdd=True)
        shadowInfo = history.retrieve(selector=None, countPurged=True)

        zvc_method = self._getZVCRepo().checkinResource
        try:
            return self._applyOrCheckin(
                zvc_method, history_id, shadowInfo, object, referenced_data, metadata
            )
        except VersionControlError:
            # this shouldn't really happen
            raise StorageSaveError(
                "Saving the object with history id '%s' failed. "
                "The underlying storage implementation reported an error." % history_id
            )

    security.declarePrivate("retrieve")

    def retrieve(self, history_id, selector=None, countPurged=True, substitute=True):
        """See ``IStorage`` and Comments in ``IPurgePolicy``"""
        zvc_repo = self._getZVCRepo()
        zvc_histid, zvc_selector = self._getZVCAccessInfo(
            history_id, selector, countPurged
        )

        if zvc_histid is None:
            raise StorageRetrieveError(
                "Retrieving version '%s' of object with history id '%s' "
                "failed. A history with the given history id does not exist."
                % (selector, history_id)
            )

        if zvc_selector is None:
            raise StorageRetrieveError(
                "Retrieving version '%s' of object with history id '%s' "
                "failed. The version does not exist." % (selector, history_id)
            )

        # retrieve the object
        try:
            zvc_obj = zvc_repo.getVersionOfResource(zvc_histid, zvc_selector)
        except VersionControlError:
            # this should never happen
            raise StorageRetrieveError(
                "Retrieving version '%s' of object with history id '%s' "
                "failed. The underlying storage implementation reported "
                "an error." % (selector, history_id)
            )

        # retrieve metadata
        # TODO: read this from the shadow storage directly
        metadata = self._retrieveMetadataFromZVC(zvc_histid, zvc_selector)

        # wrap object and referenced data
        object = zvc_obj.getWrappedObject()
        # Get referenced data from shadow history
        history = self._getShadowHistory(history_id)
        referenced_data = history.retrieve(selector).get("referenced_data", {})
        data = VersionData(object, referenced_data, metadata)

        # check if retrieved a replacement for a removed object and
        # if so check if a substitute is available
        if substitute and isinstance(data.object, Removed):
            # delegate retrieving to purge policy if one is available
            # if none is available just return the replacement for the
            # removed object
            policy = getToolByName(self, "portal_purgepolicy", None)
            if policy is not None:
                data = policy.retrieveSubstitute(history_id, selector, default=data)
        return data

    security.declarePrivate("getHistory")

    def getHistory(self, history_id, countPurged=True, substitute=True):
        """See IStorage."""
        return LazyHistory(self, history_id, countPurged, substitute)

    security.declarePrivate("getModificationDate")

    def getModificationDate(
        self, history_id, selector=None, countPurged=True, substitute=True
    ):
        """See IStorage."""
        vdata = self.retrieve(history_id, selector, countPurged, substitute)
        return vdata.object.object.modified()

    # -------------------------------------------------------------------
    # methods implementing IPurgeSupport
    # -------------------------------------------------------------------

    security.declarePrivate("purge")

    def purge(self, history_id, selector, metadata={}, countPurged=True):
        """See ``IPurgeSupport``"""
        zvc_repo = self._getZVCRepo()
        zvc_histid, zvc_selector = self._getZVCAccessInfo(
            history_id, selector, countPurged
        )
        if zvc_histid is None:
            raise StoragePurgeError(
                "Purging version '%s' of object with history id '%s' "
                "failed. A history with the given history id does not exist."
                % (selector, history_id)
            )

        if zvc_selector is None:
            raise StoragePurgeError(
                "Purging version '%s' of object with history id '%s' "
                "failed. The version does not exist." % (selector, history_id)
            )

        # digging into ZVC internals:
        # Get a reference to the version stored in the ZVC history storage
        #
        # Implementation Note:
        #
        # ZVCs ``getVersionOfResource`` is quite more complex. But as we
        # do not use labeling and branches it is not a problem to get the
        # version in the following simple way.
        zvc_history = zvc_repo.getVersionHistory(zvc_histid)
        version = zvc_history.getVersionById(zvc_selector)
        data = version._data

        if not isinstance(data.getWrappedObject(), Removed):
            # purge version in shadow storages history
            history = self._getShadowHistory(history_id)

            # update administrative data
            history.purge(selector, metadata, countPurged)

            # prepare replacement for the deleted object and metadata
            removedInfo = Removed("purged", metadata)

            # digging into ZVC internals: remove the stored object
            version._data = ZVCAwareWrapper(removedInfo, metadata)

            # digging into ZVC internals: replace the message
            logEntry = self._retrieveZVCLogEntry(zvc_histid, zvc_selector)
            logEntry.message = self._encodeMetadata(metadata)

    # -------------------------------------------------------------------
    # private helper methods
    # -------------------------------------------------------------------

    def _applyOrCheckin(
        self, zvc_method, history_id, shadowInfo, object, referenced_data, metadata
    ):
        """Just centralizing similar code."""
        # delegate the decision if and what to purge to the purge policy
        # tool if one exists. If the call returns ``False`` do not save
        # or register the current version.
        policy = getToolByName(self, "portal_purgepolicy", None)
        if policy is not None:
            if not policy.beforeSaveHook(history_id, object, metadata):
                # returning None signalizes that the version wasn't saved
                return None

        # calculate the approximate size taking into account the object
        # and the referenced_data (overwriting the archivists size as the
        # storage knows it better)
        approxSize = getSize(object) + getSize(referenced_data)
        metadata["sys_metadata"]["approxSize"] = approxSize

        # prepare the object for beeing saved with ZVC
        #
        # - Recall the ``__vc_info__`` from the most current version
        #   (selector=None).
        # - Wrap the object, the referenced data and metadata
        vc_info = self._getVcInfo(object, shadowInfo)
        zvc_obj = ZVCAwareWrapper(object, metadata, vc_info)
        message = self._encodeMetadata(metadata)

        # call appropriate ZVC method
        zvc_method(zvc_obj, message)

        # save the ``__vc_info__`` attached by the zvc call from above
        # and cache the metadata in the shadow storage
        shadowInfo = {
            "vc_info": zvc_obj.__vc_info__,
            "metadata": metadata,
            "referenced_data": referenced_data,
        }
        history = self._getShadowHistory(history_id, autoAdd=True)
        return history.save(shadowInfo)

    def _getShadowStorage(self, autoAdd=True):
        """Returns the Shadow Storage

        Returns None if there wasn't ever saved any version yet.
        """
        if self._shadowStorage is None:
            if not autoAdd:
                return None
            self._shadowStorage = ShadowStorage()
        return self._shadowStorage

    security.declarePrivate("getHistoryMetadata")

    def getHistoryMetadata(self, history_id):
        """Return the metadata blob from ShadowHistory for presenting
        summary information, etc.
        """
        if history_id is None:
            return []
        hist = self._getShadowHistory(history_id)
        if hist is None:
            return []
        return hist

    def _getShadowHistory(self, history_id, autoAdd=False):
        """Returns a History from the Shadow Storage"""
        return self._getShadowStorage().getHistory(history_id, autoAdd)

    def _getZVCRepo(self):
        """Returns the Zope Version Control Repository

        Instantiates one with the first call.
        """
        if self.zvc_repo is None:
            self.zvc_repo = ZopeRepository("repo", "ZVC Storage")
        return self.zvc_repo

    def _getZVCAccessInfo(self, history_id, selector, countPurged):
        """Returns the ZVC history id and selector

        Returns a tuple with the ZVC history id and selector.
        Returns None as history id if such history doesn't exist.
        Returns None as selector if the version does not exist.
        """
        history = self._getShadowHistory(history_id)
        if history is None:
            # no history
            return None, None

        shadowInfo = history.retrieve(selector, countPurged)
        if shadowInfo is None:
            # no version
            return False, None

        # history and version exists
        zvc_hid = shadowInfo["vc_info"].history_id
        zvc_vid = str(history.getVersionId(selector, countPurged) + 1)
        return zvc_hid, zvc_vid

    def _getVcInfo(self, obj, shadowInfo, set_checked_in=False):
        """Recalls ZVC Related Informations and Attaches them to the Object"""
        vc_info = deepCopy(shadowInfo["vc_info"])
        if vc_info is None:
            return None

        # fake sticky information (no branches)
        vc_info.sticky = None

        # On revert operations the repository expects the object
        # to be in CHECKED_IN state.
        if set_checked_in:
            vc_info.status = vc_info.CHECKED_IN
        else:
            vc_info.status = vc_info.CHECKED_OUT

        # fake the version to be able to save a retrieved version later
        zvc_repo = self._getZVCRepo()
        obj.__vc_info__ = vc_info
        vc_info.version_id = str(len(zvc_repo.getVersionIds(obj)))
        return vc_info

    def _retrieveZVCLogEntry(self, zvc_histid, zvc_selector):
        """Retrieves the metadata from ZVCs log

        Unfortunately this may get costy with long histories.
        We should really store metadata in the shadow storage in the
        future or loop over the log in reverse.

        XXX also store (only store) the metadata in the shadow before 1.0beta1
        """
        zvc_repo = self._getZVCRepo()
        log = zvc_repo.getVersionHistory(zvc_histid).getLogEntries()
        checkin = LogEntry.ACTION_CHECKIN
        entries = [
            e for e in log if e.version_id == zvc_selector and e.action == checkin
        ]

        # just make a log entry if something wrong happened
        if len(entries) != 1:
            logger.log(
                logging.INFO,
                "CMFEditions ASSERT:"
                "Uups, an object has been stored %s times with the same "
                "history '%s'!!!" % (len(entries), zvc_selector),
            )

        return entries[0]

    def _encodeMetadata(self, metadata):
        # metadata format is:
        #    - first line with trailing \x00: comment or empty comment
        #    - then: pickled metadata (incl. comment)
        try:
            comment = metadata["sys_metadata"]["comment"]
            comment = dumps(comment)
        except KeyError:
            comment = ""
        return b"\x00\n".join((comment, dumps(metadata, HIGHEST_PROTOCOL)))

    def _retrieveMetadataFromZVC(self, zvc_histid, zvc_selector):
        logEntry = self._retrieveZVCLogEntry(zvc_histid, zvc_selector)
        metadata = loads(logEntry.message.split(b"\x00\n", 1)[1])
        return metadata

    # -------------------------------------------------------------------
    # ZMI methods
    # -------------------------------------------------------------------

    security.declareProtected(ManagePortal, "zmi_getStorageStatistics")

    def zmi_getStorageStatistics(self):
        """ """
        startTime = time.time()
        # get all history ids (incl. such that were deleted in the portal)
        storage = self._getShadowStorage(autoAdd=False)
        if storage is not None:
            historyIds = storage._storage
        else:
            historyIds = {}
        hidhandler = getToolByName(self, "portal_historyidhandler")
        portal_paths_len = len(getToolByName(self, "portal_url")())

        # collect interesting informations
        histories = []
        for hid in historyIds.keys():
            history = self.getHistory(hid)
            length = len(history)
            shadowStorage = self._getShadowHistory(hid)
            size = 0
            sizeState = "n/a"
            if shadowStorage is not None:
                size, sizeState = shadowStorage.getSize()

            workingCopy = hidhandler.unrestrictedQueryObject(hid)
            if workingCopy is not None:
                url = workingCopy.absolute_url()
                path = url[portal_paths_len:]
                portal_type = workingCopy.getPortalTypeName()
            else:
                path = None
                url = None
                object_ = self.retrieve(hid).object
                if isinstance(object_, Removed):
                    portal_type = "Removed"
                else:
                    portal_type = object_.object.getPortalTypeName()
            histData = {
                "history_id": hid,
                "length": length,
                "url": url,
                "path": path,
                "portal_type": portal_type,
                "size": size,
                "sizeState": sizeState,
            }
            histories.append(histData)

        # collect history ids with still existing working copies
        existing = []
        existingHistories = 0
        existingVersions = 0
        existingSize = 0
        deleted = []
        deletedHistories = 0
        deletedVersions = 0
        deletedSize = 0
        for histData in histories:
            if histData["path"] is None:
                deleted.append(histData)
                deletedHistories += 1
                deletedVersions += histData["length"]
                deletedSize += 0  # TODO
            else:
                existing.append(histData)
                existingHistories += 1
                existingVersions += histData["length"]
                existingSize += 0  # TODO

        processingTime = "%.2f" % round(time.time() - startTime, 2)
        histories = existingHistories + deletedHistories
        versions = existingVersions + deletedVersions

        if histories:
            totalAverage = "%.1f" % round(float(versions) / histories, 1)
        else:
            totalAverage = "n/a"

        if existingHistories:
            existingAverage = "%.1f" % round(
                float(existingVersions) / existingHistories, 1
            )
        else:
            existingAverage = "n/a"

        if deletedHistories:
            deletedAverage = "%.1f" % round(
                float(deletedVersions) / deletedHistories, 1
            )
        else:
            deletedAverage = "n/a"

        return {
            "existing": existing,
            "deleted": deleted,
            "summaries": {
                "time": processingTime,
                "totalHistories": histories,
                "totalVersions": versions,
                "totalAverage": totalAverage,
                "existingHistories": existingHistories,
                "existingVersions": existingVersions,
                "existingAverage": existingAverage,
                "deletedHistories": deletedHistories,
                "deletedVersions": deletedVersions,
                "deletedAverage": deletedAverage,
            },
        }


InitializeClass(ZVCStorageTool)


class ShadowStorage(Persistent):
    """Container for Shadow Histories

    Only cares about containerish operations.
    """

    def __init__(self):
        # Using an OOBtree to allow history ids of any type. The type
        # of the history ids highly depends on the unique id tool which
        # isn't under our control.
        self._storage = OOBTree()

    def isRegistered(self, history_id):
        """Returns True if a History With the Given History id Exists"""
        if history_id is None:
            return False
        return history_id in self._storage

    def getHistory(self, history_id, autoAdd=False):
        """Returns the History Object of the Given ``history_id``.

        Returns None if ``autoAdd`` is False and the history
        does not exist. Else prepares and returns an empty history.
        """
        if history_id is None:
            return None
        # Create a new history if there isn't one yet
        if autoAdd and not self.isRegistered(history_id):
            self._storage[history_id] = ShadowHistory()
        return self._storage.get(history_id, None)


InitializeClass(ShadowStorage)


class ShadowHistory(Persistent):
    """Purge Aware History for Storage Related Metadata"""

    security = ClassSecurityInfo()

    def __init__(self):
        # Using a IOBtree as we know the selectors are integers.
        # The full history contains shadow data for every saved version.
        # A counter is needed as IOBTree doesn't have a list like append.
        self._full = IOBTree()
        self.nextVersionId = 0

        # Indexes to the full histories versions
        self._available = []

        # aproximative size of the history
        self._approxSize = 0
        self._sizeInaccurate = False

    def save(self, data):
        """Saves data in the history

        Returns the version id of the saved version.
        """
        version_id = self.nextVersionId
        referenced = {}
        # Store referenced data as is
        if "referenced_data" in data:
            referenced = data["referenced_data"]
            del data["referenced_data"]
        self._full[version_id] = deepCopy(data)
        self._full[version_id]["referenced_data"] = referenced
        self._available.append(version_id)
        # Provokes a write conflict if two saves happen the same
        # time. That's exactly what's desired.
        self.nextVersionId += 1

        # update the histories size:
        size = data["metadata"]["sys_metadata"].get("approxSize", None)
        if size is None:
            self._sizeInaccurate = True
        else:
            self._approxSize += size

        return version_id

    security.declareProtected(AccessPreviousVersions, "retrieve")

    def retrieve(self, selector, countPurged=True):
        """Retrieves the Selected Data From the History

        The caller has to make a copy if he passed the data to another
        caller.

        Returns None if the selected version does not exist.
        """
        version_id = self.getVersionId(selector, countPurged)
        if version_id is None:
            return None
        return self._full[version_id]

    def purge(self, selector, data, countPurged):
        """Purge selected version from the history"""
        # find the position to purge
        version_pos = self._getVersionPos(selector, countPurged)
        version_id = self._available[version_pos]

        # update the histories size
        sys_metadata = self._full[version_id]["metadata"]["sys_metadata"]
        size = sys_metadata.get("approxSize", None)
        if size is None:
            self._sizeInaccurate = True
        else:
            self._approxSize -= size
            if self._approxSize < 0:
                self._approxSize = 0
                self._sizeInaccurate = True

        # update the metadata
        self._full[version_id]["metadata"] = deepCopy(data)
        # purge the reference
        del self._available[version_pos]
        try:
            del self._full[version_id]["referenced_data"]
            self._full._p_changed = True
        except KeyError:
            pass

    security.declareProtected(AccessPreviousVersions, "getLength")

    def getLength(self, countPurged):
        """Length of the History Either Counting Purged Versions or Not"""
        if countPurged:
            return self.nextVersionId
        else:
            return len(self._available)

    def __len__(self):
        # Policy: The length is the entire length, including purged
        return self.getLength(True)

    def getSize(self):
        """Returns the size including the quality of the size"""
        # don't like exceptions taking down CMFEditions
        if getattr(self, "_sizeInaccurate", None) is None:
            return 0, "not available"
        if self._sizeInaccurate:
            return self._approxSize, "inaccurate"
        else:
            return self._approxSize, "approximate"

    def getVersionId(self, selector, countPurged):
        """Returns the Effective Version id depending the selector type

        Returns ``None`` if the selected version does not exist.
        """
        if selector is not None:
            selector = int(selector)

        # looking at special selectors first (None, negative)
        length = self.getLength(countPurged)
        # checking for ``None`` selector (youngest version)
        if selector is None:
            return length - 1
        # checking if positive selector tries to look into future
        if selector >= length:
            return None
        # check if negative selector and if it looks to far into past
        if selector < 0:
            selector = length + selector
            if selector < 0:
                return None

        # normal cases (0 <= selectors < length)
        if countPurged:
            # selector is a normal selector
            return selector
        else:
            # selector is a positional selector
            return self._available[selector]

    def _getVersionPos(self, selector, countPurged):
        """Returns the Position in the Version History

        The position returned does not count purged versions.
        """
        if not countPurged:
            if selector is None:
                # version counting starts with 0
                selector = self.getLength(countPurged=False) - 1
            return int(selector)

        # Lets search from the end of the available list as it is more
        # likely that a younger versions position has to be returned.
        # Let's work on a copy to not trigger an unecessary ZODB store
        # operations.
        history = self._available[:]
        history.reverse()
        try:
            selector = len(history) - 1 - history.index(selector)
        except ValueError:
            selector = None
        return selector


InitializeClass(ShadowHistory)


class ZVCAwareWrapper(Persistent):
    """ZVC assumes the stored object has a getPhysicalPath method.

    ZVC, arghh ...
    """

    def __init__(self, object, metadata, vc_info=None):
        self._object = object
        self._physicalPath = metadata["sys_metadata"].get("physicalPath", ())[:]  # copy
        if vc_info is not None:
            self.__vc_info__ = vc_info

    def getWrappedObject(self):
        return self._object

    def getPhysicalPath(self):
        return self._physicalPath


InitializeClass(ZVCAwareWrapper)


class Removed(Persistent):
    """Indicates that removement of data"""

    def __init__(self, reason, metadata):
        """Store Removed Info"""
        self.reason = reason
        self.metadata = metadata


@implementer(IVersionData)
class VersionData:
    def __init__(self, object, referenced_data, metadata):
        self.object = object
        self.referenced_data = referenced_data
        self.metadata = metadata

    def isValid(self):
        """Returns True if Valid (not Purged)"""
        return not isinstance(self.object, Removed)


@implementer(
    IHistory,
)
class LazyHistory:
    """Lazy history adapter."""

    def __init__(self, storage, history_id, countPurged=True, substitute=True):
        """See IHistory."""
        history = storage._getShadowHistory(history_id)
        if history is None:
            self._length = 0
        else:
            self._length = history.getLength(countPurged)
        self._history_id = history_id
        self._countPurged = countPurged
        self._substitute = substitute
        self._retrieve = storage.retrieve

    def __len__(self):
        """See IHistory."""
        return self._length

    def __getitem__(self, selector):
        """See IHistory."""
        return self._retrieve(
            self._history_id, selector, self._countPurged, self._substitute
        )

    def __iter__(self):
        """See IHistory."""
        return GetItemIterator(self.__getitem__, stopExceptions=(StorageRetrieveError,))


class GetItemIterator:
    """Iterator object using a getitem implementation to iterate over."""

    def __init__(self, getItem, stopExceptions):
        self._getItem = getItem
        self._stopExceptions = stopExceptions
        self._pos = -1
        self.next = self.__next__  # In order to keep compatibility with Python 2

    def __iter__(self):
        return self

    def __next__(self):
        self._pos += 1
        try:
            return self._getItem(self._pos)
        except self._stopExceptions:
            raise StopIteration()
