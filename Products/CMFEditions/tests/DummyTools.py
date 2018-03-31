# -*- coding: utf-8 -*-

from Acquisition import aq_base
from copy import deepcopy
from DateTime import DateTime
from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.ArchivistTool import ObjectData
from Products.CMFEditions.ArchivistTool import ObjectManagerStorageAdapter
from Products.CMFEditions.ArchivistTool import PreparedObject
from Products.CMFEditions.ArchivistTool import VersionData
from Products.CMFEditions.interfaces.IArchivist import ArchivistError
from Products.CMFEditions.interfaces.IPurgePolicy import IPurgePolicy
from Products.CMFEditions.interfaces.IStorage import IPurgeSupport
from Products.CMFEditions.interfaces.IStorage import IStorage
from Products.CMFEditions.interfaces.IStorage import StorageRetrieveError
from Products.CMFEditions.interfaces.IStorage import StorageUnregisteredError
from Products.CMFEditions.interfaces.IStorage import IStreamableReference
from Products.CMFEditions.utilities import dereference

from six import BytesIO
from six.moves.cPickle import Pickler
from six.moves.cPickle import Unpickler
from zope.interface import implementer

import types


# Make alog module level so that it survives transaction rollbacks
alog = []


class Dummy(SimpleItem):

    def __init__(self):
        now = DateTime()
        self.modification_date = now

    def modified(self):
        return self.modification_date

    def notifyModified(self):
        self.modification_date = DateTime()


class UniqueIdError(Exception):
    pass

class DummyBaseTool(SimpleItem):
    def getId(self):
        return self.id

def deepCopy(obj):
    stream = BytesIO()
    p = Pickler(stream, 1)
    p.dump(obj)
    stream.seek(0)
    u = Unpickler(stream)
    return u.load()

def notifyModified(obj):
    """Notify the object as modified.

    Sleeps as long as DateTime delivers a different time then
    notifies the object as modified (faster than time.sleep(2)).
    """
    t = obj.modified()
    while t == DateTime(): pass
    obj.notifyModified()


class DummyArchivist(SimpleItem):
    """Archivist simulating modifiers and history storage.
    """
    id = 'portal_archivist'

    def getId(self):
        return self.id

    def __init__(self):
        self._archive = {}
        self._counter = 0
        self.reset_log()
        self.alog_indent = ''

    def log(self, msg):
        alog.append(msg)

    def get_log(self):
        return "\n".join(alog)

    def reset_log(self):
        global alog
        alog = []

    def prepare(self, obj, app_metadata=None, sys_metadata={}):
        obj, history_id = dereference(obj)
        if history_id is None:
            # object isn't under version control yet
            # An working copy beeing under version control needs to have
            # a history_id, version_id (starts with 0) and a location_id
            # (the current implementation isn't able yet to handle multiple
            # locations. Nevertheless lets set the location id to a well
            # known default value)
            portal_hidhandler = getToolByName(obj, 'portal_historyidhandler')
            history_id = portal_hidhandler.register(obj)
            version_id = obj.version_id = 0
            obj.location_id = 0
            is_registered = False
        else:
            version_id = len(self.queryHistory(obj))
            is_registered = True

        base_obj = aq_base(obj)
        doc1_inside = getattr(base_obj, 'doc1_inside', None)
        doc2_inside = getattr(base_obj, 'doc2_inside', None)
        doc3_outside = getattr(base_obj, 'doc3_outside', None)

        # simulate clone modifiers
        icrefs = []
        ocrefs = []
        clone = deepCopy(base_obj)
        if doc1_inside is not None:
            icrefs.append(ObjectManagerStorageAdapter(clone, 'doc1_inside'))
        if doc2_inside is not None:
            icrefs.append(ObjectManagerStorageAdapter(clone, 'doc2_inside'))
        if doc3_outside is not None:
            ocrefs.append(ObjectManagerStorageAdapter(clone, 'doc3_outside'))
        crefs = icrefs + ocrefs

        # simulate before save modifier
        iorefs = []
        oorefs = []
        if doc1_inside is not None:
            iorefs.append(getattr(obj, 'doc1_inside'))
        if doc2_inside is not None:
            iorefs.append(getattr(obj, 'doc2_inside'))
        if doc3_outside is not None:
            oorefs.append(getattr(obj, 'doc3_outside'))
        orefs = iorefs + oorefs
        for cref in crefs:
            cref.setAttribute(VersionAwareReference())

        # log
        if sys_metadata['originator'] is None:
            self.log("")
        if orefs:
            self.log("%sprepare %s: hid=%s, refs=(%s)"
                        % (self.alog_indent,
                           obj.getId(),
                           history_id,
                           ', '.join([ref.getId() for ref in orefs])))
        else:
            self.log("%sprepare %s: hid=%s"
                        % (self.alog_indent, obj.getId(), history_id))
        self.alog_indent += '  '

        # prepare object structure
        original_info = ObjectData(obj, iorefs, oorefs)
        clone_info = ObjectData(clone, icrefs, ocrefs)

        approxSize = None

        return PreparedObject(history_id, original_info, clone_info, (),
                              app_metadata, sys_metadata, is_registered, approxSize)

    def register(self, prepared_obj):
        # log
        self.log("%sregister %s: hid=%s, is_registered=%s"
                    % (self.alog_indent,
                       prepared_obj.original.object.getId(),
                       prepared_obj.history_id,
                       prepared_obj.is_registered))

        if not prepared_obj.is_registered:
            # new empty history
            self._archive[prepared_obj.history_id] = []
            self.save(prepared_obj)

    def save(self, prepared_obj, autoregister=False):
        if not prepared_obj.is_registered:
            if not autoregister:
                raise ArchivistError("not registered: %s " % prepared_obj.original.object)
            self._archive[prepared_obj.history_id] = []

        # log
        self.alog_indent = self.alog_indent[0:-2]

        irefs = [ref.getAttribute() for ref in prepared_obj.clone.inside_refs]
        orefs = [ref.getAttribute() for ref in prepared_obj.clone.outside_refs]
        irefs_prep = ['{hid:%s, vid:%s}' % (r.history_id, r.version_id)
                      for r in irefs]
        orefs_prep = ['{hid:%s, vid:%s}' % (r.history_id, r.version_id)
                      for r in orefs]
        irefs = ', '.join(irefs_prep)
        orefs = ', '.join(orefs_prep)
        if irefs:
            irefs = "irefs=(%s), " % irefs
        if orefs:
            orefs = "orefs=(%s), " % orefs
        refs = irefs + orefs
        self.log("%ssave    %s: hid=%s, %sisreg=%s, auto=%s"
                    % (self.alog_indent,
                       prepared_obj.original.object.getId(),
                       prepared_obj.history_id,
                       refs,
                       prepared_obj.is_registered,
                       autoregister))

        # save in the format the data needs to be retrieved
        svdata = {
            'clone': prepared_obj.clone,
            'referenced_data': prepared_obj.referenced_data,
            'metadata': prepared_obj.metadata,
        }
        # storage simulation
        self._archive[prepared_obj.history_id].append(svdata)

    def retrieve(self, obj=None, history_id=None, selector=None, preserve=(),
                 countPurged=True):
        obj, history_id = dereference(obj, history_id, self)
        if selector is None:
            selector = len(self._archive[history_id]) - 1  #HEAD

        self.log("%sretrieve %s: hid=%s, selector=%s"
                    % (self.alog_indent, obj.getId(), history_id, selector))

        data = self._archive[history_id][selector]
        attr_handling_references = ['_objects','_tree','_count','_mt_index', '__annotations__']
        attr_handling_references.extend(data['clone'].object.objectIds())
        attr_handling_references.extend(obj.objectIds())
        vdata = VersionData(data['clone'],
                    [],
                    attr_handling_references,
                    data['referenced_data'],
                    data['metadata'])

        return deepCopy(vdata)

    def getHistory(self, obj=None, history_id=None, preserve=()):
        obj, history_id = dereference(obj, history_id, self)
        return [deepCopy(obj) for obj in self._archive[history_id]]

    def getHistoryMetadata(self, obj=None, history_id=None):
        obj, history_id = dereference(obj, history_id, self)
        return [item['metadata'] for item in self._archive[history_id]]

    def queryHistory(self, obj=None, history_id=None,
                     preserve=(), default=None):
        if default is None:
            default = []
        try:
            history = self.getHistory(obj=obj, history_id=history_id, preserve=preserve)
        except KeyError:
            return default
        if history:
            return history
        return default

    def isUpToDate(self, obj=None, history_id=None, selector=None):
        obj = dereference(obj=obj, history_id=history_id, zodb_hook=self)[0]
        mem = self.retrieve(obj=obj, history_id=history_id, selector=selector)
        return mem.data.object.modified() == obj.modified()


class VersionAwareReference:
    def __init__(self, **info):
        self.history_id = None
        self.version_id = None
        self.info = info

    def setReference(self, target_obj, remove_info=True):
        portal_hidhandler = getToolByName(target_obj, 'portal_historyidhandler')
        portal_archivist = getToolByName(target_obj, 'portal_archivist')
        self.history_id = portal_hidhandler.queryUid(target_obj)
        self.version_id = len(portal_archivist.queryHistory(target_obj))-1
        self.location_id = 1 # only one location possible currently
        if remove_info and hasattr(self, 'info'):
            self.info = None

    def __of__(self, parent):
        return self


class DummyModifier(DummyBaseTool):
    id = 'portal_modifier'

    def beforeSaveModifier(self, obj, clone):
        return {}, [], [] # XXX 2nd and 3rd shall be lists

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        preserved = {}
        # just a dead simple test implementation
        for key in preserve:
            preserved[key] = key
        return [], [], preserved

    def getReferencedAttributes(self, obj):
        return {}

    def reattachReferencedAttributes(self, object, referenced_data):
        # nothing to do
        return

    def getOnCloneModifiers(self, obj):
        return None

class FolderishContentObjectModifier(DummyBaseTool):
    """This is a full fledged modifier.
    """

    id = 'portal_modifier'

    def getReferencedAttributes(self, obj):
        # we declare the title beeing a big blob we don't want to be
        # pickled and unpickled by the archivist
        return {'title': obj.title}

    def getOnCloneModifiers(self, obj):
        """Removes childrens ending with '_inside' or '_outside'.

        Just replaces object manager sub objects ending '_inside' or
        '_outside' by a uninitialzed 'IVersionAwareReference'.
        All other childrens get versioned with the parent.
        """
        portal_archivist = getToolByName(obj, 'portal_archivist')
        VersionAwareReference = portal_archivist.classes.VersionAwareReference

        # do not pickle the object managers subobjects
        refs = {}
        outside_refs = []
        inside_refs = []
        for name, sub in obj.objectItems():
            pyid = id(aq_base(sub))
            if name.endswith('_inside'):
                inside_refs.append(sub)
                refs[pyid] = True
            elif name.endswith('_outside'):
                outside_refs.append(sub)
                refs[pyid] = True

        # do not pickle the big blob attributes
        base_obj = aq_base(obj)
        for attr in self.getReferencedAttributes(obj).keys():
            try:
                pyid = id(getattr(base_obj, attr))
            except AttributeError:
                pass
            else:
                refs[pyid] = False

        def persistent_id(obj):
            if id(obj) in refs:
                return id(obj)
            return None

        def persistent_load(pid):
            if pid in refs:
                if refs[pid]:
                    # references
                    return VersionAwareReference()
                else:
                    # just directly passed attributes
                    return None
            # should never reach this!
            assert False

        return persistent_id, persistent_load, inside_refs, outside_refs, ''

    def beforeSaveModifier(self, obj, clone):
        """Returns all unititialized 'IVersionAwareReference' objects.

        This allways goes in conjunction with 'getOnCloneModifiers'.
        """
        portal_archivist = getToolByName(obj, 'portal_archivist')
        AttributeAdapter = portal_archivist.classes.AttributeAdapter

        # just return adapters to the attributes that were replaced by
        # a uninitialzed 'IVersionAwareReference' object
        outside_refs = []
        inside_refs = []
        for name in clone.objectIds():
            if name.endswith('_inside'):
                inside_refs.append(AttributeAdapter(clone, name))
            elif name.endswith('_outside'):
                outside_refs.append(AttributeAdapter(clone, name))

        return {}, inside_refs, outside_refs

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        preserved = {}
        # just a dead simple test implementation
        for key in preserve:
            preserved[key] = key

        ref_names = self._getAttributeNamesHandlingSubObjects(obj)
        return [], ref_names, {}

    def reattachReferencedAttributes(self, object, referenced_data):
        # just a dead simple test implementation
        for key, value in referenced_data.items():
            setattr(object, key, value)

    def _getAttributeNamesHandlingSubObjects(self, obj):
        return ['_objects', '_tree', '_count', '_mt_index', '__annotations__'].extend(obj.objectIds())


class DummyHistoryIdHandler(DummyBaseTool):
    id = 'portal_historyidhandler'

    UID_ATTRIBUTE_NAME = 'editions_uhid'

    uhid_counter = 0

    UniqueIdError = UniqueIdError

    objectRegistry = {}

    def register(self, obj):
        uhid = self.queryUid(obj)
        if uhid is None:
            self.uhid_counter += 1
            uhid = self.uhid_counter
            setattr(obj, self.UID_ATTRIBUTE_NAME, uhid)
            self.objectRegistry[uhid] = obj
        return uhid

    def queryUid(self, obj, default=None):
        return getattr(aq_base(obj), self.UID_ATTRIBUTE_NAME, default)

    def getUid(self, obj):
        uid = self.queryUid(obj, default=None)
        if uid is None:
            raise UniqueIdError("'%s' has no unique id attached." % obj)
        return uid

    def queryObject(self, uid, default=None):
        try:
            return self.objectRegistry[uid]
        except KeyError:
            return default

#    def setUid(self, obj, uid, check_uniqueness=True):
#        setattr(obj, self.UID_ATTRIBUTE_NAME, uid)

class StorageVersionData:
    def __init__(self, object, referenced_data, metadata):
        self.object = object
        self.referenced_data = referenced_data
        self.metadata = metadata
    def isValid(self):
        return not isinstance(self.object, Removed)

class Removed:
    """Indicates that removement of data
    """

    def __init__(self, reason, metadata):
        """Store Removed Info
        """
        self.reason = reason
        self.metadata = metadata

@implementer(IStorage, IPurgeSupport)
class MemoryStorage(DummyBaseTool):
    id = 'portal_historiesstorage'


    def __init__(self):
        self._histories = {}

    def register(self, history_id, object, referenced_data={}, metadata=None):
        histories = self._histories
        if history_id not in histories.keys():
           return self._save(history_id, object, referenced_data, metadata)

    def save(self, history_id, object, referenced_data={}, metadata=None):
        # delegate the decission what to purge to the purge policy tool
        # if it exists. If the call returns ``True`` do not save the current
        # version.
        policy = getToolByName(self, 'portal_purgepolicy', None)
        if policy is not None:
            if not policy.beforeSaveHook(history_id, metadata):
                return len(self._histories[history_id]) - 1

        if not history_id in self._histories:
            raise StorageUnregisteredError(
                "Saving or retrieving an unregistered object is not "
                "possible. Register the object with history id '%s' first. "
                % history_id)

        return self._save(history_id, object, referenced_data, metadata)


    def _save(self, history_id, object, referenced_data={}, metadata=None):
        histories = self._histories
        cloned_referenced_data = {}

        for key, ref in referenced_data.items():
            # a real storage may treat IStreamableReference obj differently
            if IStreamableReference.providedBy(ref):
                cloned_referenced_data[key] = deepCopy(ref.getObject())
            else:
                cloned_referenced_data[key] = deepCopy(ref)
        vdata = StorageVersionData(object=deepCopy(object),
                                   referenced_data=cloned_referenced_data,
                                   metadata=metadata)
        if history_id in histories.keys():
            histories[history_id].append(vdata)
        else:
            histories[history_id] = [vdata]

        return len(histories[history_id]) - 1

    def retrieve(self, history_id, selector=None,
                 countPurged=True, substitute=True):
        if selector is None:
            selector = len(self._getHistory(history_id)) - 1

        if countPurged:
            try:
                vdata = self._getHistory(history_id)[selector]
            except IndexError:
                raise StorageRetrieveError("Retrieving non existing version %s"
                                           % selector)

            vdata.referenced_data = deepcopy(vdata.referenced_data)
            if substitute and isinstance(vdata.object, Removed):
                # delegate retrieving to purge policy if one is available
                # if none is available just return "the removed object"
                policy = getToolByName(self, 'portal_purgepolicy', None)
                if policy is not None:
                    vdata = policy.retrieveSubstitute(history_id, selector, vdata)
            return vdata
        else:
            valid = 0
            history = self._getHistory(history_id)
            for vdata in history:
                if isinstance(vdata.object, Removed):
                    continue
                if valid == selector:
                    return vdata
                valid += 1
            raise StorageRetrieveError("Retrieving non existing version %s"
                                       % selector)

    def getHistory(self, history_id, preserve=(), countPurged=True,
                   substitute=True):
        history = []
        sel = 0

        while True:
            try:
                vdata = self.retrieve(history_id, sel, countPurged, substitute)
            except StorageRetrieveError:
                break
            history.append(vdata)
            sel += 1

        return HistoryList(history)

    def getHistoryMetadata(self, history_id):
        return self.getHistory(history_id)

    def isRegistered(self, history_id):
        return history_id in self._histories

    def getModificationDate(self, history_id, selector=None,
                            countPurged=True, substitute=True):
        vdata = self.retrieve(history_id, selector, countPurged, substitute)
        return vdata.object.object.modified()

    def purge(self, history_id, selector, metadata={}, countPurged=True):
        """See ``IPurgeSupport``
        """
        histories = self._histories
        history = histories[history_id]
        vdata = self.retrieve(history_id, selector, countPurged,
                              substitute=False)
        selector = history.index(vdata)
        if not isinstance(vdata.object, Removed):
            # prepare replacement for the deleted object and metadata
            removedInfo = Removed("purged", metadata)

            # digging into ZVC internals: remove the stored object
            history[selector] = StorageVersionData(removedInfo, None, metadata)

    def _getHistory(self, history_id):
        try:
            history = self._histories[history_id]
        except KeyError:
            raise StorageUnregisteredError(
                "Saving or retrieving an unregistered object is not "
                "possible. Register the object with history id '%s' first. "
                % history_id)
        return history
#        return HistoryList(history)

    def _getLength(self, history_id, countPurged=True):
        """Returns the length of the history
        """
        histories = self._histories
        history = self._getHistory(history_id)
        if countPurged:
            return len(history)

        length = 0
        for vdata in history:
            if not isinstance(vdata.object, Removed):
                length += 1

        return length


class HistoryList(types.ListType):
    """
    """
    def __getitem__(self, selector):
        if selector is None:
            selector = -1
        try:
           return types.ListType.__getitem__(self, selector)
        except IndexError:
            raise StorageRetrieveError("Retrieving non existing version %s" % selector)

    def retrieve(self, selector, ignored=True):
       """Faux metadata only retrieval"""
       item = self[selector]
       return {'metadata': item.metadata}

@implementer(IPurgePolicy)
class DummyPurgePolicy(DummyBaseTool):
    """Dummy Purge Policy
    """
    id = 'portal_purgepolicy'

    def beforeSaveHook(self, history_id, obj, metadata={}):
        """Purge old versions

        Purges old version so that at maximum two versions reside in
        the history.
        """
        storage = getToolByName(self, 'portal_historiesstorage')
        currentVersion = len(storage.getHistory(history_id))
        while True:
            length = len(storage.getHistory(history_id, countPurged=False))
            if length < 2:
                break
            comment = "purged on save of version %s" % currentVersion
            metadata = {"sys_metadata": {"comment": comment}}
            storage.purge(history_id, 0, metadata, countPurged=False)

        return True

    def retrieveSubstitute(self, history_id, selector, default=None):
        """Retrives the next older version
        """
        storage = getToolByName(self, 'portal_historiesstorage')
        while selector:
            selector -= 1
            data = storage.retrieve(history_id, selector, substitute=False)
            if data.isValid():
                return data
        return default


@implementer(IStorage, IPurgeSupport)
class PurgePolicyTestDummyStorage(DummyBaseTool):
    """Partial Storage used for PurgePolicy Tetss
    """
    id = 'portal_historiesstorage'

    def __init__(self):
        self.history = []

    def save(self, history_id, obj):
        self.history.append(obj)

    def getHistory(self, history_id, preserve=(), countPurged=True,
                   substitute=True):
        return self.history

    def purge(self, history_id, selector, metadata={},
              countPurged=True):
        del self.history[selector]

    def retrieve(self, history_id, selector=None,
                 countPurged=True, substitute=True):
        if selector >= len(self.history):
            raise StorageRetrieveError()
        return self.history[selector]


class DummyData(object):
    def __init__(self, data):
        self.data = data

    def isValid(self):
        return True


class RemovedData(object):
    def isValid(self):
        return False
