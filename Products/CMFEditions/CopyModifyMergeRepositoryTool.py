# -*- coding: utf-8 -*-
#########################################################################
# Copyright (c) 2004, 2005 Alberto Berti, Gregoire Weber,
# Reflab (Vincenzo Di Somma, Francesco Ciriaci, Riccardo Lemmi)
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
"""Copy Modify Merge Repository implementation.

$Id: CopyModifyMergeRepositoryTool.py,v 1.20 2005/06/24 11:42:01 gregweb Exp $
"""

import time
import transaction

from App.class_init import InitializeClass
from Acquisition import aq_base, aq_parent, aq_inner
from Acquisition import ImplicitAcquisitionWrapper
from AccessControl import ClassSecurityInfo, Unauthorized
from OFS.SimpleItem import SimpleItem
from BTrees.OOBTree import OOBTree
from zope.event import notify
from zope.interface import implements, Interface
from zope.lifecycleevent import ObjectModifiedEvent
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.utils import _checkPermission

from Products.CMFEditions.utilities import dereference, wrap
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError

from Products.CMFEditions.interfaces.IRepository import ICopyModifyMergeRepository
from Products.CMFEditions.interfaces.IRepository import IPurgeSupport
from Products.CMFEditions.interfaces.IRepository import RepositoryPurgeError
from Products.CMFEditions.interfaces.IRepository import IContentTypeVersionPolicySupport
from Products.CMFEditions.interfaces.IRepository import IRepositoryTool
from Products.CMFEditions.interfaces.IRepository import IVersionData
from Products.CMFEditions.interfaces.IRepository import IHistory

from Products.CMFEditions.interfaces.IModifier import ModifierException

from Products.CMFEditions.Permissions import ApplyVersionControl
from Products.CMFEditions.Permissions import SaveNewVersion
from Products.CMFEditions.Permissions import PurgeVersion
from Products.CMFEditions.Permissions import AccessPreviousVersions
from Products.CMFEditions.Permissions import RevertToPreviousVersions
from Products.CMFEditions.Permissions import ManageVersioningPolicies
from Products.CMFEditions.VersionPolicies import VersionPolicy
from Products.CMFEditions.utilities import STUB_OBJECT_PREFIX

try:
    from Products.Archetypes.event import ObjectEditedEvent
    from Products.Archetypes.interfaces import IBaseObject
except ImportError:
    class IBaseObject(Interface):
        pass

try:
    from Products.Archetypes.interfaces.referenceable import IReferenceable
    from Products.Archetypes.config import (
        REFERENCE_ANNOTATION as REFERENCES_CONTAINER_NAME)
    from Products.Archetypes.exceptions import ReferenceException
    WRONG_AT = False
    HAVE_Z3_IFACE = issubclass(IReferenceable, Interface)
except ImportError:
    WRONG_AT = True


VERSIONABLE_CONTENT_TYPES = []
VERSION_POLICY_MAPPING = {}
VERSION_POLICY_DEFS = {}
HOOKS = {'add': 'setupPolicyHook',
         'remove': 'removePolicyHook',
         'enable': 'enablePolicyOnTypeHook',
         'disable': 'disablePolicyOnTypeHook'}

class CopyModifyMergeRepositoryTool(UniqueObject,
                                    SimpleItem):

    """See ICopyModifyMergeRepository
    """

    implements(
        IPurgeSupport,
        ICopyModifyMergeRepository,
        IContentTypeVersionPolicySupport,
        IRepositoryTool,
        )

    id = 'portal_repository'
    alternative_id = 'portal_copymergerepository'

    meta_type = 'CMFEditions Standard Copy Modify Merge Repository'

    autoapply = True

    security = ClassSecurityInfo()

    manage_options = SimpleItem.manage_options[1:]

    _versionable_content_types = VERSIONABLE_CONTENT_TYPES
    _version_policy_mapping = VERSION_POLICY_MAPPING
    _policy_defs = VERSION_POLICY_DEFS

    # Method for migrating the default dict to a per instance OOBTree,
    # performed on product install.
    def _migrateVersionPolicies(self):
        if not isinstance(self._policy_defs, OOBTree):
            btree_defs = OOBTree()
            for obj_id, title in self._policy_defs.items():
                btree_defs[obj_id] = VersionPolicy(obj_id, title)
            self._policy_defs = btree_defs

    # -------------------------------------------------------------------
    # methods implementing IContentTypeVersionPolicySupport
    # -------------------------------------------------------------------

    security.declarePublic('isVersionable')
    def isVersionable(self, obj):
        """See interface.
        """
        return obj.portal_type in self.getVersionableContentTypes()

    security.declarePublic('getVersionableContentTypes')
    def getVersionableContentTypes(self):
        return self._versionable_content_types

    security.declareProtected(ManageVersioningPolicies, 'setVersionableContentTypes')
    def setVersionableContentTypes(self, new_content_types):
        self._versionable_content_types = new_content_types

    # XXX: There was a typo which mismatched the interface def, preserve it
    # for backwards compatibility
    security.declareProtected(ManageVersioningPolicies, 'setVersionableContentType')
    setVersionableContentType = setVersionableContentTypes

    security.declareProtected(ManageVersioningPolicies, 'addPolicyForContentType')
    def addPolicyForContentType(self, content_type, policy_id, **kw):
        assert policy_id in self._policy_defs, "Unknown policy %s" % policy_id
        policies = self._version_policy_mapping.copy()
        cur_policy = policies.setdefault(content_type, [])
        if policy_id not in cur_policy:
            cur_policy.append(policy_id)
            self._callPolicyHook('enable', policy_id, content_type, **kw)
        self._version_policy_mapping = policies

    security.declareProtected(ManageVersioningPolicies, 'removePolicyFromContentType')
    def removePolicyFromContentType(self, content_type, policy_id, **kw):
        policies = self._version_policy_mapping.copy()
        cur_policy = policies.setdefault(content_type, [])
        if policy_id in cur_policy:
            cur_policy.remove(policy_id)
            self._callPolicyHook('disable', policy_id, content_type, **kw)
        self._version_policy_mapping = policies

    security.declarePublic('supportsPolicy')
    def supportsPolicy(self, obj, policy):
        content_type = obj.portal_type
        # in 1.0alpha3 and earlier ``version_on_revert`` was
        # ``version_on_rollback``. Convert to new name.
        config = self._version_policy_mapping.get(content_type, [])
        if "version_on_rollback" in config:
            config[config.index("version_on_rollback")] = "version_on_revert"

        return policy in self._version_policy_mapping.get(content_type, [])

    security.declarePublic('hasPolicy')
    def hasPolicy(self, obj):
        content_type = obj.portal_type
        return bool(self._version_policy_mapping.get(content_type, None))

    security.declareProtected(ManageVersioningPolicies, 'manage_setTypePolicies')
    def manage_setTypePolicies(self, policy_map, **kw):
        assert isinstance(policy_map, dict)
        for p_type, policies in self._version_policy_mapping.items():
            for policy_id in list(policies):
                self.removePolicyFromContentType(p_type, policy_id, **kw)
        for p_type, policies in policy_map.items():
            assert isinstance(policies, list), \
                "Policy list for %s must be a list" % str(p_type)
            for policy_id in policies:
                assert policy_id in self._policy_defs, \
                    "Policy %s is unknown" % policy_id
                self.addPolicyForContentType(p_type, policy_id, **kw)

    security.declarePublic('listPolicies')
    def listPolicies(self):
        # convert the internal dict into a sequence of tuples
        # sort on title
        policy_list = [(p.Title(), p) for p in self._policy_defs.values()]
        policy_list.sort()
        policy_list = [p for (title, p) in policy_list]
        return policy_list

    security.declareProtected(ManageVersioningPolicies, 'addPolicy')
    def addPolicy(self, policy_id, policy_title,
                  policy_class=VersionPolicy, **kw):
        self._policy_defs[policy_id] = policy_class(policy_id, policy_title)
        self._callPolicyHook('add', policy_id, **kw)

    security.declareProtected(ManageVersioningPolicies, 'removePolicy')
    def removePolicy(self, policy_id, **kw):
        for p_type in self._version_policy_mapping.keys():
            self.removePolicyFromContentType(p_type, policy_id, **kw)
        self._callPolicyHook('remove', policy_id, **kw)
        del self._policy_defs[policy_id]

    security.declareProtected(ManageVersioningPolicies, 'manage_changePolicyDefs')
    def manage_changePolicyDefs(self, policy_list, **kwargs):
        # Call remove hooks for existing policies
        p_defs = self._policy_defs
        for policy_id in list(p_defs.keys()):
            self.removePolicy(policy_id, **kwargs)
        # Verify proper input formatting
        assert isinstance(policy_list, list) or isinstance(policy_list, tuple)
        for item in policy_list:
            assert isinstance(item, tuple), \
                "List items must be tuples: %s" % str(item)
            assert len(item) in (2, 3, 4), \
                "Each policy definition must contain a title and id: %s" % str(item)
            assert isinstance(item[0], basestring), \
                "Policy id must be a string: %s" % str(item[0])
            assert isinstance(item[1], basestring), \
                "Policy title must be a string: %s" % str(item[1])
            # Get optional Policy class and kwargs.
            if len(item) >= 3:
                policy_class = item[2]
            else:
                policy_class = VersionPolicy
            if len(item) == 4:
                assert isinstance(item[3], dict), \
                    "Extra args for %s must be a dict" % item[0]
                kw = item[3]
            else:
                kw = kwargs
            # Add new policy
            self.addPolicy(item[0], item[1], policy_class, **kw)

    security.declareProtected(ManageVersioningPolicies, 'getPolicyMap')
    def getPolicyMap(self):
        return dict(self._version_policy_mapping)

    def _callPolicyHook(self, action, policy_id, *args, **kw):
        # in 1.0alpha3 and earlier ``version_on_revert`` was
        # ``version_on_rollback``. Convert to new name.
        if policy_id == "version_on_revert":
            if "version_on_rollback" in self._policy_defs:
                value = self._policy_defs["version_on_rollback"]
                self._policy_defs["version_on_revert"] = value
                del self._policy_defs["version_on_rollback"]

        hook = getattr(self._policy_defs[policy_id], HOOKS[action], None)
        if hook is not None and callable(hook):
            portal = getToolByName(self, 'portal_url').getPortalObject()
            hook(portal, *args, **kw)

    # -------------------------------------------------------------------
    # methods implementing ICopyModifyMergeRepository
    # -------------------------------------------------------------------

    security.declareProtected(ApplyVersionControl, 'setAutoApplyMode')
    def setAutoApplyMode(self, autoapply):
        """See ICopyModifyMergeRepository.
        """
        self.autoapply = autoapply

    security.declarePublic('applyVersionControl')
    def applyVersionControl(self, obj, comment='', metadata={}):
        """See ICopyModifyMergeRepository.
        """
        self._assertAuthorized(obj, ApplyVersionControl, 'applyVersionControl')
        sp = transaction.savepoint(optimistic=True)
        try:
            self._recursiveSave(obj, metadata,
                                self._prepareSysMetadata(comment),
                                autoapply=True)
        except ModifierException:
            # modifiers can abort save operations under certain conditions
            sp.rollback()
            raise

    security.declarePublic('save')
    def save(self, obj, comment='', metadata={}):
        """See ICopyModifyMergeRepository.
        """
        self._assertAuthorized(obj, SaveNewVersion, 'save')
        sp = transaction.savepoint(optimistic=True)
        try:
            self._recursiveSave(obj, metadata,
                                self._prepareSysMetadata(comment),
                                autoapply=self.autoapply)
        except ModifierException:
            # modifiers can abort save operations under certain conditions
            sp.rollback()
            raise

    # -------------------------------------------------------------------
    # methods implementing IPurgeSupport
    # -------------------------------------------------------------------

    security.declarePublic('purge')
    def purge(self, obj, selector, comment="", metadata={}, countPurged=True):
        """See IPurgeSupport.
        """
        self._assertAuthorized(obj, PurgeVersion, 'purge')

        # Trying to avoid mess with purged versions which we don't offer
        # support yet when passed to the repository layer due to a missing
        # purge policy. The problem would occure on revert and retrieve.
        pp = getToolByName(self, 'portal_purgepolicy', None)
        if pp is None:
            raise RepositoryPurgeError("Purging a version is not possible. "
                                       "Purge is only possible with a purge "
                                       "policy installed.")

        portal_archivist = getToolByName(self, 'portal_archivist')
        # just hand over to the archivist for the moment (recursive purging
        # may be implemented in a future release)
        metadata = {
            "app_metadata": metadata,
            "sys_metadata": self._prepareSysMetadata(comment),
        }
        portal_archivist.purge(obj=obj, selector=selector,
                               metadata=metadata, countPurged=countPurged)

    security.declarePublic('revert')
    def revert(self, obj, selector=None, countPurged=True):
        """See IPurgeSupport.
        """
        # XXX this should go away if _recursiveRetrieve is correctly implemented
        original_id = obj.getId()

        self._assertAuthorized(obj, RevertToPreviousVersions, 'revert')
        fixup_queue = []
        self._recursiveRetrieve(obj=obj, selector=selector, inplace=True,
                                fixup_queue=fixup_queue,
                                countPurged=countPurged)
        # XXX this should go away if _recursiveRetrieve is correctly implemented
        if obj.getId() != original_id:
            obj._setId(original_id)
            # parent.manage_renameObject(obj.getId(), original_id)
            # parent._setObject(original_id, obj, set_owner=0)

        # run fixups
        self._doInplaceFixups(fixup_queue, True)

    security.declarePublic('retrieve')
    def retrieve(self, obj, selector=None, preserve=(), countPurged=True):
        """See IPurgeSupport.
        """
        self._assertAuthorized(obj, AccessPreviousVersions, 'retrieve')
        return self._retrieve(obj, selector, preserve, countPurged)

    security.declarePublic('restore')
    def restore(self, history_id, selector, container, new_id=None,
                countPurged=True):
        """See IPurgeSupport.
        """

        self._assertAuthorized(container, RevertToPreviousVersions, 'revert')
        fixup_queue = []
        vdata = self._recursiveRetrieve(history_id=history_id,
                                        selector=selector, inplace=True,
                                        source=container,
                                        fixup_queue=fixup_queue,
                                        ignore_existing=True,
                                        countPurged=countPurged)

        # Set the id to the desired value
        orig_id = vdata.data.object.getId()
        if new_id and orig_id != new_id:
            # Make sure we have a _p_jar
            transaction.savepoint()
            container.manage_renameObject(orig_id, new_id)
            # parent._setObject(original_id, obj, set_owner=0)

        # run fixups
        self._doInplaceFixups(fixup_queue, True)

    security.declarePublic('getHistory')
    def getHistory(self, obj, oldestFirst=False, preserve=(),
                   countPurged=True):
        """See IPurgeSupport.
        """
        self._assertAuthorized(obj, AccessPreviousVersions, 'getHistory')
        return LazyHistory(self, obj, oldestFirst, preserve, countPurged)

    security.declarePublic('getHistoryMetadata')
    def getHistoryMetadata(self, obj):
        """Returns the versioning metadata history.
        """
        self._assertAuthorized(obj, AccessPreviousVersions,
                               'getHistoryMetadata')
        portal_archivist = getToolByName(self, 'portal_archivist')
        hist = portal_archivist.getHistoryMetadata(obj)
        if hist:
            return ImplicitAcquisitionWrapper(hist, obj)
        return hist


    security.declarePublic('isUpToDate')  # noqa
    def isUpToDate(self, obj, selector=None, countPurged=True):
        """See IPurgeSupport.
        """
        portal_archivist = getToolByName(self, 'portal_archivist')
        return portal_archivist.isUpToDate(obj=obj, selector=selector,
                                           countPurged=countPurged)

    # -------------------------------------------------------------------
    # private helper methods
    # -------------------------------------------------------------------

    def _assertAuthorized(self, obj, permission, name=None):
        # We need to provide access to the repository upon the object
        # permissions istead of repositories method permissions.
        # So the repository method access is set to public and the
        # access is check on the object when needed.
        if not _checkPermission(permission, obj):
            raise Unauthorized(name)

    def _prepareSysMetadata(self, comment):
        return {
            # comment is system metadata
            'comment': comment,
            # setting a timestamp here set the same timestamp at all
            # recursively saved objects
            'timestamp': time.time(),
            # None means the current object is the originator of the
            # save or purge operation
            'originator': None,
        }

    def _recursiveSave(self, obj, app_metadata, sys_metadata, autoapply):
        # prepare the save of the originating working copy
        portal_archivist = getToolByName(self, 'portal_archivist')
        prep = portal_archivist.prepare(obj, app_metadata, sys_metadata)

        # set the originator of the save operation for the referenced
        # objects
        if sys_metadata['originator'] is None:
            clone = prep.clone.object
            sys_metadata['originator'] = "%s.%s.%s" % (prep.history_id,
                                                       clone.version_id,
                                                       clone.location_id, )

        # What comes now is the current hardcoded policy:
        #
        # - recursively save inside references, then set a version aware
        #   reference
        # - on outside references only set a version aware reference
        #   (if under version control)
        inside_refs = map(lambda original_refs, clone_refs:
                          (original_refs, clone_refs.getAttribute()),
                          prep.original.inside_refs, prep.clone.inside_refs)
        for orig_ref, clone_ref in inside_refs:
            self._recursiveSave(orig_ref, app_metadata, sys_metadata,
                                autoapply)
            clone_ref.setReference(orig_ref, remove_info=True)

        outside_refs = map(lambda oref, cref: (oref, cref.getAttribute()),
                           prep.original.outside_refs, prep.clone.outside_refs)
        for orig_ref, clone_ref in outside_refs:
            clone_ref.setReference(orig_ref, remove_info=True)

        portal_archivist.save(prep, autoregister=autoapply)

        # just to ensure that the working copy has the correct
        # ``version_id``
        prep.copyVersionIdFromClone()

    def _retrieve(self, obj, selector, preserve, countPurged):
        """Retrieve a former state.

        Puts the returned version into same context as the working copy is
        (to make attribute access acquirable).
        """
        # We make a savepoint so that we can undo anything that happened
        # during the transaction.  There may be resource managers which do not
        # support savepoints, those will raise errors here, which means that
        # retrieve and getHistory should not be used as a part of more
        # complex transactions.
        saved = transaction.savepoint()
        vd = self._recursiveRetrieve(obj=obj, selector=selector,
                                     preserve=preserve, inplace=False,
                                     countPurged=countPurged)
        saved.rollback()
        wrapped = wrap(vd.data.object, aq_parent(aq_inner(obj)))
        return VersionData(wrapped, vd.preserved_data,
                           vd.sys_metadata, vd.app_metadata)

    def _recursiveRetrieve(self, obj=None, history_id=None, selector=None, preserve=(),
                           inplace=False, source=None, fixup_queue=None,
                           ignore_existing=False, countPurged=True):
        """This is the real workhorse pulling objects out recursively.
        """
        portal_archivist = getToolByName(self, 'portal_archivist')
        portal_reffactories = getToolByName(self, 'portal_referencefactories')
        if ignore_existing:
            obj = None
        else:
            obj, history_id = dereference(obj, history_id, self)

        hasBeenDeleted = obj is None

        # CMF's invokeFactory needs the added object be traversable from
        # itself to the root and from the root to the itself. This is the
        # reason why it is necessary to replace the working copies current
        # state with the one of the versions state retrieved. If the
        # operation is not an inplace operation (retrieve instead of
        # revert) this has to be reversed after having recursed into the
        # tree.
        if hasBeenDeleted:
            # if the object to retreive doesn't have a counterpart in the tree
            # build a new one before retrieving an old state
            vdata = portal_archivist.retrieve(obj, history_id, selector,
                                              preserve, countPurged)
            repo_clone = vdata.data.object
            obj = portal_reffactories.invokeFactory(repo_clone, source)
            hasBeenMoved = False
        else:
            if source is None:
                # #### the source has to be stored with the object at save time
                # I(gregweb)'m pretty sure the whole source stuff here gets
                # obsolete as soon as a va_ref to the source is stored also
                # XXX for now let's stick with this:
                source = aq_parent(aq_inner(obj))

            # in the special case the object has been moved the retrieved
            # object has to get a new history (it's like copying back back
            # the object and then retrieve an old state)
            hasBeenMoved = portal_reffactories.hasBeenMoved(obj, source)

        if hasBeenMoved:
            if getattr(aq_base(source), obj.getId(), None) is None:
                vdata = portal_archivist.retrieve(obj, history_id, selector,
                                                  preserve, countPurged)
                repo_clone = vdata.data.object
                obj = portal_reffactories.invokeFactory(repo_clone, source)
            else:
                # What is the desired behavior
                pass

        vdata = portal_archivist.retrieve(obj, history_id, selector,
                                          preserve, countPurged)

        # Replace the objects attributes retaining identity.
        _missing = object()
        attrs_to_leave = vdata.attr_handling_references
        for key, val in vdata.data.object.__dict__.items():
            if key in attrs_to_leave:
                continue
            obj_val = getattr(aq_base(obj), key, _missing)  # noqa
            setattr(obj, key, val)

        # Delete reference attributes.
        for ref in vdata.refs_to_be_deleted:
            ref.remove(permanent=inplace)

        # retrieve all inside refs
        for attr_ref in vdata.data.inside_refs:
            # get the referenced working copy
            # XXX if the working copy we're searching for was moved to
            # somewhere else *outside* we generate an another object with
            # the same history_id. Unfortunately we're not able to handle
            # this correctly before multi location stuff is implemented.
            # XXX Perhaps there is a need for a workaround!
            va_ref = attr_ref.getAttribute()
            if va_ref is None:
                # a missing reference, the policy has changed,
                # don't try to replace it
                continue
            history_id = va_ref.history_id

            # retrieve the referenced version (always count purged versions
            # also!)
            ref_vdata = self._recursiveRetrieve(history_id=history_id,
                                                selector=va_ref.version_id,
                                                preserve=(),
                                                inplace=inplace,
                                                source=obj,
                                                fixup_queue=fixup_queue,
                                                ignore_existing=ignore_existing,
                                                countPurged=True)

            # reattach the python reference
            attr_ref.setAttribute(ref_vdata.data.object)

        # reattach all outside refs to the current working copy
        # XXX this is an implicit policy we can live with for now
        for attr_ref in vdata.data.outside_refs:
            va_ref = attr_ref.getAttribute()
            cur_value = attr_ref.getAttribute(alternate=obj)
            # If the attribute has been removed by a modifier, then we get
            # None, move on to the next ref.
            if va_ref is None:
                continue
            try:
                ref = dereference(history_id=va_ref.history_id, zodb_hook=self)[0]
            except (TypeError, AttributeError):
                # get the attribute from the working copy
                ref = cur_value
            # If the object is not under version control just attach
            # the current working copy if it exists and is not already
            # in place
            if ref is not None and aq_base(ref) is not aq_base(va_ref):
                attr_ref.setAttribute(ref)

        # feed the fixup queue defined in revert() and retrieve() to
        # perform post-retrieve fixups on the object
        if fixup_queue is not None:
            fixup_queue.append(obj)
        return vdata

    def _doInplaceFixups(self, queue, inplace):
        """ Perform fixups to deal with implementation details
        (especially zodb and cmf details) which need to be done in
        each retrieved object."""
        for obj in queue:
            if inplace:
                if not WRONG_AT:
                    self._fixupATReferences(obj)
                self._fixIds(obj)
                self._fixupCatalogData(obj)

    def _fixupCatalogData(self, obj):
        """ Reindex the object, otherwise the catalog will certainly
        be out of sync."""
        portal_catalog = getToolByName(self, 'portal_catalog')
        portal_catalog.indexObject(obj)
        notify(ObjectModifiedEvent(obj))
        if IBaseObject.providedBy(obj):
            notify(ObjectEditedEvent(obj))
        # XXX: In theory we should probably be emitting IObjectMoved event
        # here as it is a possible consequence of a revert.
        # Perhaps in our current meager z2 existence we should do
        # obj.manage_afterRename()? Also, should we be doing obj.indexObject()
        # instead to make sure we maximally cover specialized classes which
        # want to handle their cataloging in special ways (this has the
        # side-effect of changing the modification date of the reverted
        # object).

    def _fixupATReferences(self, obj):
        """Reindex AT reference data, and delete reference
        implementations when the target
        doesn't exist anymore.

        Deletion of references is done at the end of the
        recursiveRetrieve operation to avoid deleting refs to targets
        that will be retrieved later in the recursiveRetrive. It
        doesn't call refcatalog.deleteReference as that method uses
        brains to retrieve reference implementations. If the
        target doesn't exist, brains for references pointing to it
        do not exist either.

        This manually calls reference.delHook to let it finalize
        correctly but traps ReferenceException eventually emitted in
        the process and forces the deletion, because leaving the
        reference impl. there will leave refcatalog in an
        incosistent state.
        """

        if (HAVE_Z3_IFACE and IReferenceable.providedBy(obj)
                or not HAVE_Z3_IFACE and IReferenceable.isImplementedBy(obj)) \
                and hasattr(obj, REFERENCES_CONTAINER_NAME):
            # Delete refs if their target doesn't exists anymore
            ref_folder = getattr(obj, REFERENCES_CONTAINER_NAME)
            uid_catalog = getToolByName(self, 'uid_catalog')
            ref_catalog = getToolByName(self, 'reference_catalog')
            ref_objs = ref_folder.objectValues()
            for ref in ref_objs:
                if not uid_catalog(UID=ref.targetUID):
                    try:
                        # at's _deleteReference passes the catalog
                        # itself, the source and target obj... i'm
                        # going to emulate it as much as i can
                        ref.delHook(ref_catalog, obj, None)
                    except ReferenceException:
                        pass
                    ref_folder.manage_delObjects(ref.getId())
            # then reindex references
            container = aq_parent(aq_inner(obj))
            obj._updateCatalog(container)

    def _fixIds(self, obj):
        items = getattr(obj, 'objectItems', None)
        if callable(items):
            temp_ids = []
            # find sub-objects whose id doesn't match the name in the container
            # remove them from the folder temporarily. This could probably be made
            # more efficient.  We assume that any id inconsistencies were created by
            # us, and fix accordingly.
            for orig_id, child in items():
                real_id = child.getId()
                if orig_id != real_id:
                    obj._delOb(orig_id)
                    object_list = getattr(obj, '_objects', None)
                    if object_list is not None:
                        obj._objects = tuple([o for o in object_list if o['id'] != orig_id])  # noqa
                    temp_ids.append((real_id, child))
            # Make a second pass to move the objects into place if possible
            all_ids = list(obj.objectIds())
            for new_id, child in temp_ids:
                if new_id not in all_ids:
                    # XXX: This calls child.manage_afterAdd, and it's not clear that we
                    # should do so, perhaps manually manipulating the _objects is the
                    # better way to go.
                    obj._setObject(new_id, child)
                    all_ids.append(new_id)
                else:
                    # If we really can't add the object make the temp_id permanent
                    temp_id = new_id + STUB_OBJECT_PREFIX
                    child.id = temp_id
                    obj._setObject(temp_id, child)
                    all_ids.append(temp_id)

    # -------------------------------------------------------------------
    # diagnostics support
    # -------------------------------------------------------------------

    def createTestHierarchy(self, context):
        """Create a Content Test Hierarchy
        """
        # XXX to be allowed in test mode only
        from StorageMigrationSupport import createTestHierarchy
        createTestHierarchy(context)


class VersionData:
    """
    """
    implements(IVersionData)

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, object, preserved_data, sys_metadata, app_metadata):
        self.object = object
        self.preserved_data = preserved_data
        self.comment = sys_metadata.get('comment', '')
        self.metadata = app_metadata
        self.sys_metadata = sys_metadata
        # If access contents information is disabled for anonymous on the object,
        # then a problem arises when trying to access its attributes.  So we
        # need to make version_id available (if only this were Zope 3) ;)
        self.version_id = object.version_id


class LazyHistory:
    """Lazy history.
    """
    implements(IHistory)

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, repository, obj, oldestFirst, preserve, countPurged):
        archivist = getToolByName(repository, 'portal_archivist')
        self._repo = repository
        self._obj = obj
        self._oldestFirst = oldestFirst
        self._preserve = preserve
        self._countPurged = countPurged
        self._retrieve = repository._retrieve
        self._length = len(archivist.queryHistory(obj=obj, preserve=preserve,
                                                  countPurged=countPurged))
        self._cache = {}

    def __len__(self):
        """See IHistory
        """
        return self._length

    def __getitem__(self, selector):
        """See IHistory
        """
        if not self._oldestFirst and selector < self._length:
            if selector >= 0:
                selector = self._length - 1 - selector
            else:
                selector = - (selector + 1)
        if selector in self._cache:
            return self._cache[selector]

        result = self._cache[selector] = self._retrieve(
            self._obj, selector, self._preserve, self._countPurged)
        return result

    def __iter__(self):
        """See IHistory.
        """
        return GetItemIterator(self.__getitem__,
                               stopExceptions=(ArchivistRetrieveError,))


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


InitializeClass(CopyModifyMergeRepositoryTool)
