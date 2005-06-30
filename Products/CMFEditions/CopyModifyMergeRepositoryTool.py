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

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError

from Products.CMFEditions.interfaces.IRepository import ICopyModifyMergeRepository
from Products.CMFEditions.interfaces.IRepository import IVersionData, IHistory

from Products.CMFEditions.Permissions import ApplyVersionControl
from Products.CMFEditions.Permissions import SaveNewVersion
from Products.CMFEditions.Permissions import AccessPreviousVersions
from Products.CMFEditions.Permissions import RevertToPreviousVersions
from Products.CMFEditions.Permissions import CheckoutToLocation

VERSIONABLE_CONTENT_TYPES = []

class CopyModifyMergeRepositoryTool(UniqueObject, SimpleItem, ActionProviderBase):
    """
    """
    __implements__ = (
        SimpleItem.__implements__,
        ICopyModifyMergeRepository,
    )

    id = 'portal_repository'
    alternative_id = 'portal_copymergerepository'

    meta_type = 'CMFEditions Standard Copy Modify Merge Repository'

    autoapply = False

    security = ClassSecurityInfo()

    manage_options = (ActionProviderBase.manage_options
                     + SimpleItem.manage_options[1:]
                     )

    _versionable_content_types = VERSIONABLE_CONTENT_TYPES

    # -------------------------------------------------------------------
    # private helper methods
    # -------------------------------------------------------------------

    def _assertAuthorized(self, obj, permission, name=None):
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
        inside_refs = map(lambda oref, cref: (oref, cref.getAttribute()),
                          prep.original.inside_refs, prep.clone.inside_refs)
        for orig_ref, clone_ref in inside_refs:
            self._recursiveSave(orig_ref, app_metadata, sys_metadata,
                                autoapply)
            clone_ref.setReference(orig_ref, remove_info=True)

        outside_refs = map(lambda oref, cref: (oref, cref.getAttribute()),
                           prep.original.outside_refs, prep.clone.outside_refs)
        for orig_ref, clone_ref in outside_refs:
            clone_ref.setReference(orig_ref, remove_info=True)

        # save the originating working copy
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

    # -------------------------------------------------------------------
    # methods implementing IArchivist
    # -------------------------------------------------------------------

    security.declarePublic('isVersionable')
    def isVersionable(self, obj):
        """See IVersioning.
        """
        return obj.portal_type in self.getVersionableContentTypes()

    def getVersionableContentTypes(self):
        return self._versionable_content_types

    def setVersionableContentType(self, new_content_types):
        self._versionable_content_types = new_content_types

    security.declareProtected(ApplyVersionControl, 'setAutoApplyMode')
    def setAutoApplyMode(self, autoapply):
        """
        """
        self.autoapply = autoapply

    security.declarePublic('ApplyVersionControl')
    def applyVersionControl(self, obj, comment='', metadata={}):
        """
        """
        self._assertAuthorized(obj, ApplyVersionControl, 'applyVersionControl')
        self._recursiveSave(obj, metadata,
                            self._prepareSysMetadata(comment),
                            autoapply=True)

    security.declarePublic('save')
    def save(self, obj, comment='', metadata={}):
        """
        """
        self._assertAuthorized(obj, SaveNewVersion, 'save')
        self._recursiveSave(obj, metadata, 
                            self._prepareSysMetadata(comment),
                            autoapply=self.autoapply)

    security.declarePublic('revert')
    def revert(self, obj, selector=None):
        """
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
        
    security.declarePublic('retrieve')
    def retrieve(self, obj, selector=None, preserve=()):
        """
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
        """
        """
        portal_archivist = getToolByName(self, 'portal_archivist')
        return portal_archivist.isUpToDate(obj, selector)

    security.declarePublic('getHistory')
    def getHistory(self, obj, preserve=()):
        """
        """
        self._assertAuthorized(obj, AccessPreviousVersions, 'getHistory')
        parent = aq_parent(aq_inner(obj))
        return LazyHistory(self, obj, parent, preserve)

    security.declarePublic('checkout')
    def checkout(self, history_id, container, version_id=None, preserve=()):
        """
        """
        raise NotImplementedError(
              "The repositories 'checkout' method is not yet implemented")
        self._assertAuthorized(obj, CheckoutToLocation, 'checkout')

    security.declarePublic('getHistoryById')
    def getHistoryById(self, history_id):
        """
        """
        raise NotImplementedError(
              "The repositories 'getHistoryById' method is not yet implemented")
        self._assertAuthorized(obj, AccessPreviousVersions, 'getHistoryById')


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
