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

from Globals import InitializeClass
from Persistence import Persistent
from Acquisition import aq_base, aq_parent, aq_inner
from AccessControl import ClassSecurityInfo, Unauthorized
from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager
from BTrees.OOBTree import OOBTree

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError

from Products.CMFEditions.interfaces.IRepository import ICopyModifyMergeRepository
from Products.CMFEditions.interfaces.IRepository import IContentTypeVersionPolicySupport
from Products.CMFEditions.interfaces.IRepository import IVersionData
from Products.CMFEditions.interfaces.IRepository import IHistory
from Products.CMFEditions.interfaces.IRepository import IVersionPolicy

from Products.CMFEditions.Permissions import ApplyVersionControl
from Products.CMFEditions.Permissions import SaveNewVersion
from Products.CMFEditions.Permissions import AccessPreviousVersions
from Products.CMFEditions.Permissions import RevertToPreviousVersions
from Products.CMFEditions.Permissions import CheckoutToLocation
from Products.CMFEditions.Permissions import ManageVersioningPolicies

VERSIONABLE_CONTENT_TYPES = []
VERSION_POLICY_MAPPING = {}
VERSION_POLICY_DEFS = {}

class VersionPolicy(SimpleItem):
    """A simple class for storing version policy information"""

    __implements__ = (SimpleItem.__implements__,
                      IVersionPolicy
                      )
    security = ClassSecurityInfo()

    def __init__(self, obj_id, title, **kw):
        self.id = obj_id
        self.title = title

    security.declarePublic('Title')
    def Title(self):
        return self.title

class CopyModifyMergeRepositoryTool(UniqueObject,
                                    SimpleItem,
                                    ActionProviderBase):

    """See ICopyModifyMergeRepository
    """

    __implements__ = (SimpleItem.__implements__,
                      ICopyModifyMergeRepository,
                      IContentTypeVersionPolicySupport,
                      )

    id = 'portal_repository'
    alternative_id = 'portal_copymergerepository'

    meta_type = 'CMFEditions Standard Copy Modify Merge Repository'

    autoapply = True

    security = ClassSecurityInfo()

    manage_options = (ActionProviderBase.manage_options
                     + SimpleItem.manage_options[1:]
                     )

    _versionable_content_types = VERSIONABLE_CONTENT_TYPES
    _version_policy_mapping = VERSION_POLICY_MAPPING
    _policy_defs = VERSION_POLICY_DEFS

    # Method for migrating the default dict to a per instance OOBTree,
    # performed on product install.
    def _migrateVersionPolicies(self):
        if not isinstance(self._policy_defs, OOBTree):
            btree_defs = OOBTree()
            for obj_id, title in self._policy_defs.items():
                btree_defs[obj_id]=VersionPolicy(obj_id, title)
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
    def addPolicyForContentType(self, content_type, policy):
        assert self._policy_defs.has_key(policy), "Unknown policy %s"%policy
        policies = self._version_policy_mapping.copy()
        cur_policy = policies.setdefault(content_type, [])
        if policy not in cur_policy:
            cur_policy.append(policy)
        self._version_policy_mapping = policies

    security.declareProtected(ManageVersioningPolicies, 'removePolicyFromContentType')
    def removePolicyFromContentType(self, content_type, policy):
        policies = self._version_policy_mapping.copy()
        cur_policy = policies.setdefault(content_type, [])
        if policy in cur_policy:
            cur_policy.remove(policy)
        self._version_policy_mapping = policies

    security.declarePublic('supportsPolicy')
    def supportsPolicy(self, obj, policy):
        content_type = obj.portal_type
        return policy in self._version_policy_mapping.get(content_type, [])

    security.declarePublic('hasPolicy')
    def hasPolicy(self, obj):
        content_type = obj.portal_type
        return bool(self._version_policy_mapping.get(content_type, None))

    security.declareProtected(ManageVersioningPolicies, 'manage_setPolicies')
    def manage_setTypePolicies(self, policy_map):
        assert isinstance(policy_map, dict)
        for p_type, policies in policy_map.items():
            assert isinstance(policies, list), \
                            "Policy list for %s must be a list"%str(p_type)
            for policy in policies:
                assert self._policy_defs.has_key(policy), \
                                  "Policy %s is unknown"%policy
        self._version_policy_mapping = policy_map

    security.declarePublic('listPolicies')
    def listPolicies(self):
        # convert the internal dict into a sequence of tuples
        # sort on title
        policy_list = [(p.Title(), p) for p in self._policy_defs.values()]
        policy_list.sort()
        policy_list = [p for (title, p) in policy_list]
        return policy_list

    security.declareProtected(ManageVersioningPolicies, 'addPolicy')
    def addPolicy(self, policy_id, policy_title):
        self._policy_defs[policy_id]=VersionPolicy(policy_id,policy_title)
        self._p_changed = 1

    security.declareProtected(ManageVersioningPolicies, 'removePolicy')
    def removePolicy(self, policy_id):
        del self._policy_defs[policy_id]
        for policies in self._version_policy_mapping.values():
            if policy_id in policies:
                policies.remove(policy_id)
        self._p_changed = 1

    security.declareProtected(ManageVersioningPolicies, 'manage_changePolicyDefs')
    def manage_changePolicyDefs(self, policy_list):
        # Verify proper input formatting
        policy_def_mapping = OOBTree()
        assert isinstance(policy_list, list) or isinstance(policy_list, tuple)
        for item in policy_list:
            assert isinstance(item, tuple), \
                        "List items must be tuples: %s"%str(item)
            assert len(item)==2, \
            "Each policy definition must contain a title and id: %s"%str(item)
            assert isinstance(item[0], basestring), \
                        "Policy id must be a string: %s"%str(item[0])
            assert isinstance(item[1], basestring), \
                        "Policy title must be a string: %s"%str(item[1])
            policy_def_mapping[item[0]] = VersionPolicy(item[0],item[1])

        self._policy_defs = policy_def_mapping

    security.declareProtected(ManageVersioningPolicies, 'getPolicyMap')
    def getPolicyMap(self):
        return dict(self._version_policy_mapping)

    # -------------------------------------------------------------------
    # methods implementing ICopyModifyMergeRepository
    # -------------------------------------------------------------------


    security.declareProtected(ApplyVersionControl, 'setAutoApplyMode')
    def setAutoApplyMode(self, autoapply):
        """
        """
        self.autoapply = autoapply

    security.declarePublic('ApplyVersionControl')
    def applyVersionControl(self, obj, comment='', metadata={}):
        """See interface.
        """
        self._assertAuthorized(obj, ApplyVersionControl, 'applyVersionControl')
        self._recursiveSave(obj, metadata,
                            self._prepareSysMetadata(comment),
                            autoapply=True)

    security.declarePublic('save')
    def save(self, obj, comment='', metadata={}):
        """See interface.
        """
        self._assertAuthorized(obj, SaveNewVersion, 'save')
        self._recursiveSave(obj, metadata, 
                            self._prepareSysMetadata(comment),
                            autoapply=self.autoapply)

    security.declarePublic('revert')
    def revert(self, obj, selector=None):
        """See interface.
        """
        original_id = obj.getId()
        self._assertAuthorized(obj, RevertToPreviousVersions, 'revert')
        parent = aq_parent(aq_inner(obj))
        self._recursiveRetrieve(obj, parent, selector, preserve=(),
                                inplace=True)
        if obj.getId() != original_id:
            obj._setId(original_id)
            #parent.manage_renameObject(obj.getId(), original_id)
            #parent._setObject(original_id, obj, set_owner=0)

    security.declarePublic('retrieve')
    def retrieve(self, obj, selector=None, preserve=()):
        """See interface.
        """
        self._assertAuthorized(obj, AccessPreviousVersions, 'retrieve')
        parent = aq_parent(aq_inner(obj))
        vd = self._recursiveRetrieve(obj, parent, selector, preserve)

        # The object needs to be contained in the correct folder as
        # some calls (e.g. getToolByName) will insist on using containment
        # rather than context.
        wrapped = self._setContainment(vd.data.object, parent)

        return VersionData(wrapped, vd.preserved_data,
                           vd.sys_metadata, vd.app_metadata)

    security.declarePublic('isUpToDate')
    def isUpToDate(self, obj, selector=None):
        """See interface.
        """
        portal_archivist = getToolByName(self, 'portal_archivist')
        return portal_archivist.isUpToDate(obj, selector)

    security.declarePublic('getHistory')
    def getHistory(self, obj, preserve=()):
        """See interface.
        """
        self._assertAuthorized(obj, AccessPreviousVersions, 'getHistory')
        parent = aq_parent(aq_inner(obj))
        return LazyHistory(self, obj, parent, preserve)


    security.declarePublic('getObjectType') # XXX
    def getObjectType(self, history_id):
        """
        """
        portal_archivist = getToolByName(self, 'portal_archivist')
        return portal_archivist.getObjectType(history_id)

    # -------------------------------------------------------------------
    # private helper methods
    # -------------------------------------------------------------------


    def _assertAuthorized(self, obj, permission, name=None):
        #We need to provide access to the repository upon the object
        #permissions istead of repository permissions so the repository is
        #public and the access is check on the object when need.
        if not _checkPermission(permission, obj):
            raise Unauthorized(name)

    def _prepareSysMetadata(self, comment):
        return {
            # comment is system metadata
            'comment': comment,
            # setting a timestamp here set the same timestamp at all
            # recursively saved objects
            'timestamp': int(time.time()),
            # None means the current object is the originator of the
            # save operation
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

    def _recursiveRetrieve(self, obj, parent, selector, preserve=(),
                           inplace=False):
        portal_archivist = getToolByName(self, 'portal_archivist')
        portal_hidhandler = getToolByName(self, 'portal_historyidhandler')

        # The current policy implemented by the following lines of code is:
        #
        # - inside references were restored to what they referenced at
        #   save time
        # - inside referenced objects beeing moved to outside the object
        #   cause double objects with the same history_id (see XXX below,
        #   THIS IS BAD AND MUST BE SOLVED BEFORE A 1.0)
        # - outside references were restored to the current working copy
        # - this currently works only for objects implementing a
        #   'invokeFactory' method (XXX THIS IS ALSO BAD)
        vdata = portal_archivist.retrieve(obj, selector, preserve)

        # rewrap (XXX is this the correct place here in case of inplace?)
        vdata.data.object = vdata.data.object.__of__(parent)

        # -------------
        # XXX The problem here is that the following two loops 'know'
        # how to rebuild the references. Planed was that the modifiers
        # know how to rebuild the references. This layer has to know
        # about the rebuild policy only and communicate that properly
        # to the modifiers.
        # --> The archivist API has to be extended

        # retrieve all inside refs

        for attr_ref in vdata.data.inside_refs:
            # get the referenced working copy
            # XXX if the working copy we're searching for was moved to
            # somewhere else *outside* we generate an another object with
            # the same history_id. Unfortunately we're not able to handle
            # this correctly before multi location stuff is implemented.
            # XXX Perhaps there is a need for a workaround!
            va_ref = attr_ref.getAttribute()
            ref = portal_hidhandler.queryObject(va_ref.history_id, None)
            if ref is None:
                #import pdb; pdb.set_trace()
                # there is no working copy for the referenced version, so
                # create an empty object of the same type (it's only
                # temporary if not inplace).
                repo_obj = portal_archivist.getRepoObject(va_ref.history_id)
                # XXX make that more intelligent
                ref_id = "%s_CMFEDITIONSTMPIDSUFFIX" % repo_obj.getId()
                obj.invokeFactory(repo_obj.portal_type, ref_id)
                ref = getattr(obj, ref_id)
                # XXX see note above
                portal_hidhandler.setUid(ref, va_ref.history_id)
                deleteRefFromContainer = not inplace # True if not inplace
            else:
                deleteRefFromContainer = False

            # retrieve the referenced version
            ref_vdata = self._recursiveRetrieve(ref, obj, va_ref.version_id,
                                                preserve=(), inplace=inplace)

            # delete the temp object from the container if necessary
            if deleteRefFromContainer:
                obj.manage_delObjects(ids=[ref_id])

            # reattach the python reference
            attr_ref.setAttribute(ref_vdata.data.object)

        # reattach all outside refs to the current working copy
        # XXX this is an implicit policy we can live with for now
        for attr_ref in vdata.data.outside_refs:
            va_ref = attr_ref.getAttribute()
            ref = portal_hidhandler.queryObject(va_ref.history_id, None)
            if ref is None:
                ref = getattr(aq_base(obj), attr_ref.getAttributeName())
            # If the object is not under version control just
            # attach the current working copy
            attr_ref.setAttribute(ref)

        if inplace:
            # replace obj retaining identity
            #
            # An inplace copy has to preserve the object itself as we don't
            # want to manage parents and python references to it.
            # This is done by copying the retreived data over the working 
            # copies data.
            # XXX hmmm? Do we need to do the replacement recursively?
            for attr, val in vdata.data.object.__dict__.items():
                setattr(obj, attr, val)

            # reindex the object
            portal_catalog = getToolByName(self, 'portal_catalog')
            portal_catalog.reindexObject(obj)

        return vdata

    security.declarePrivate('_setContainment')
    def _setContainment(self, obj, parent):
        """Make obj be contained within parent"""
        # Cannot set the attribute directory as Python will think it
        # is a private variable and munge the name.
        tempAttribute = '__v_CMFEDITIONS_TMP'
        changed = parent._p_changed
        setattr(parent, tempAttribute, obj)
        wrapped = getattr(parent, tempAttribute)
        delattr(parent, tempAttribute)
        parent._p_changed = changed
        return wrapped


class VersionData:
    """
    """
    __implements__ = (IVersionData, )

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, object, preserved_data, sys_metadata, app_metadata):
        self.object = object
        self.preserved_data = preserved_data
        self.comment = sys_metadata.get('comment', '')
        self.metadata = app_metadata
        self.sys_metadata = sys_metadata


class LazyHistory:
    """Lazy history.
    """
    __implements__ = (IHistory, )

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, repository, obj, parent, preserve=()):
        self._repository = repository
        self._obj = obj
        self._parent = parent
        self._preserve = preserve

    def __len__(self):
        """
        """
        archivist = getToolByName(self._repository, 'portal_archivist')
        return len(archivist.queryHistory(self._obj))

    def __getitem__(self, selector):
        vd = self._repository._recursiveRetrieve(self._obj, self._parent,
                                                 selector, self._preserve)
        return VersionData(vd.data.object, vd.preserved_data,
                           vd.sys_metadata, vd.app_metadata)


    def __iter__(self):
        return GetItemIterator(self.__getitem__, ArchivistRetrieveError)


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


InitializeClass(CopyModifyMergeRepositoryTool)
