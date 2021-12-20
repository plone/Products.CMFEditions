#########################################################################
# Copyright (c) 2005 Alberto Berti, Gregoire Weber,
# Reflab(Vincenzo Di Somma, Francesco Ciriaci, Riccardo Lemmi),
# Duncan Booth
#
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
"""Standard modifiers
"""

from AccessControl.class_init import InitializeClass
from Acquisition import aq_base
from OFS.ObjectManager import ObjectManager
from plone.folder.default import DefaultOrdering
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base
from Products.CMFCore.Expression import Expression
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError
from Products.CMFEditions.interfaces.IModifier import IAttributeModifier
from Products.CMFEditions.interfaces.IModifier import ICloneModifier
from Products.CMFEditions.interfaces.IModifier import IConditionalTalesModifier
from Products.CMFEditions.interfaces.IModifier import IReferenceAdapter
from Products.CMFEditions.interfaces.IModifier import ISaveRetrieveModifier
from Products.CMFEditions.Modifiers import ConditionalModifier
from Products.CMFEditions.Modifiers import ConditionalTalesModifier
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.component.interfaces import IPossibleSite
from zope.copy import copy
from zope.interface import implementer
from zope.interface.interfaces import ComponentLookupError

import sys


_marker = []


# ----------------------------------------------------------------------
# Product initialziation, installation and factory stuff
# ----------------------------------------------------------------------


def initialize(context):
    """Registers modifiers with zope (on zope startup)."""
    for m in modifiers:
        context.registerClass(
            m["wrapper"],
            m["id"],
            permission=ManagePortal,
            constructors=(m["form"], m["factory"]),
            icon=m["icon"],
        )


def install(portal_modifier, ids=None):
    """Registers modifiers in the modifier registry (at tool install time)."""
    for m in modifiers:
        id = m["id"]
        if ids is not None and id not in ids:
            continue
        if id in portal_modifier.objectIds():
            continue
        title = m["title"]
        modifier = m["modifier"]()
        wrapper = m["wrapper"](id, modifier, title)
        enabled = m["enabled"]
        if IConditionalTalesModifier.providedBy(wrapper):
            wrapper.edit(enabled, m["condition"])
        else:
            wrapper.edit(enabled)

        portal_modifier.register(m["id"], wrapper)


manage_OMOutsideChildrensModifierAddForm = PageTemplateFile(
    "www/OMOutsideChildrensModifierAddForm.pt",
    globals(),
    __name__="manage_OMOutsideChildrensModifierAddForm",
)


def manage_addOMOutsideChildrensModifier(self, id, title=None, REQUEST=None):
    """Add an object manager modifier treating childrens as outside refs"""
    modifier = OMOutsideChildrensModifier()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_OMInsideChildrensModifierAddForm = PageTemplateFile(
    "www/OMInsideChildrensModifierAddForm.pt",
    globals(),
    __name__="manage_OMInsideChildrensModifierAddForm",
)


def manage_addOMInsideChildrensModifier(self, id, title=None, REQUEST=None):
    """Add an object manager modifier treating children as inside refs"""
    modifier = OMInsideChildrensModifier()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_RetainUIDsModifierAddForm = PageTemplateFile(
    "www/RetainUIDsModifierAddForm.pt",
    globals(),
    __name__="manage_RetainUIDsModifierAddForm",
)


def manage_addRetainUIDs(self, id, title=None, REQUEST=None):
    """Add a modifier retaining UIDs upon retrieve."""
    modifier = RetainUIDs()
    self._setObject(id, ConditionalModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_RetainWorkflowStateAndHistoryModifierAddForm = PageTemplateFile(
    "www/RetainWorkflowStateAndHistoryModifierAddForm.pt",
    globals(),
    __name__="manage_RetainWorkflowStateAndHistoryModifierAddForm",
)


def manage_addRetainWorkflowStateAndHistory(self, id, title=None, REQUEST=None):
    """Add a modifier retaining workflow state upon retrieve."""
    modifier = RetainWorkflowStateAndHistory()
    self._setObject(id, ConditionalModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_RetainPermissionsSettingsAddForm = PageTemplateFile(
    "www/RetainPermissionsSettingsModifierAddForm.pt",
    globals(),
    __name__="manage_RetainPermissionsSettingsModifierAddForm",
)


def manage_addRetainPermissionsSettings(self, id, title=None, REQUEST=None):
    """Add a modifier retaining permissions upon retrieve."""
    modifier = RetainPermissionsSettings()
    self._setObject(id, ConditionalModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_SaveFileDataInFileTypeByReferenceModifierAddForm = PageTemplateFile(
    "www/SaveFileDataInFileTypeByReferenceModifierAddForm.pt",
    globals(),
    __name__="manage_SaveFileDataInFileTypeByReferenceModifierAddForm",
)


def manage_addSaveFileDataInFileTypeByReference(self, id, title=None, REQUEST=None):
    """Add a modifier avoiding unnecessary cloning of file data."""
    modifier = SaveFileDataInFileTypeByReference()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


# silly modifier just for demos
manage_SillyDemoRetrieveModifierAddForm = PageTemplateFile(
    "www/SillyDemoRetrieveModifierAddForm.pt",
    globals(),
    __name__="manage_SillyDemoRetrieveModifierAddForm",
)


def manage_addSillyDemoRetrieveModifier(self, id, title=None, REQUEST=None):
    """Add a silly demo retrieve modifier"""
    modifier = SillyDemoRetrieveModifier()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_AbortVersioningOfLargeFilesAndImagesAddForm = PageTemplateFile(
    "www/AbortVersioningOfLargeFilesAndImagesAddForm.pt",
    globals(),
    __name__="manage_AbortVersioningOfLargeFilesAndImagesAddForm",
)


def manage_addAbortVersioningOfLargeFilesAndImages(self, id, title=None, REQUEST=None):
    """Add a silly demo retrieve modifier"""
    modifier = AbortVersioningOfLargeFilesAndImages(id, title)
    self._setObject(id, modifier)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_SkipVersioningOfLargeFilesAndImagesAddForm = PageTemplateFile(
    "www/SkipVersioningOfLargeFilesAndImagesAddForm.pt",
    globals(),
    __name__="manage_SkipVersioningOfLargeFilesAndImagesAddForm",
)


def manage_addSkipVersioningOfLargeFilesAndImages(self, id, title=None, REQUEST=None):
    """Add a silly demo retrieve modifier"""
    modifier = SkipVersioningOfLargeFilesAndImages(id, title)
    self._setObject(id, modifier)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_SkipParentPointersAddForm = PageTemplateFile(
    "www/SkipParentPointersAddForm.pt",
    globals(),
    __name__="manage_SkipParentPointersAddForm",
)


def manage_addSkipParentPointers(self, id, title=None, REQUEST=None):
    """Add a skip parent pointers modifier"""
    modifier = SkipParentPointers(id, title)
    self._setObject(id, modifier)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_SkipRegistryBasesPointersAddForm = PageTemplateFile(
    "www/SkipRegistryBasesPointersAddForm.pt",
    globals(),
    __name__="manage_SkipRegistryBasesPointersAddForm",
)


def manage_addSkipRegistryBasesPointers(self, id, title=None, REQUEST=None):
    """Add a skip component registry bases modifier"""
    modifier = SkipRegistryBasesPointers(id, title)
    self._setObject(id, modifier)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


manage_Skip_z3c_blobfileAddForm = PageTemplateFile(
    "www/Skip_z3c_blobfile.pt", globals(), __name__="manage_Skip_z3c_blobfileAddForm"
)


def manage_addSkip_z3c_blobfile(self, id, title=None, REQUEST=None):
    """Add a skip z3c.blobfile modifier"""
    modifier = Skip_z3c_blobfile(id, title)
    self._setObject(id, modifier)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(self.absolute_url() + "/manage_main")


# ----------------------------------------------------------------------
# Standard modifier implementation
# ----------------------------------------------------------------------


@implementer(ISaveRetrieveModifier)
class RetainAttributeAnnotationItemsBase:
    """Standard modifier retaining values of specific annotations from
    the working copy
    """

    PRESERVE_ANNOTATION_KEYS = ()

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # replace specific annotation elements with those from the working copy
        repo_annotations = getattr(repo_clone, "__annotations__", None)
        obj_annotations = getattr(obj, "__annotations__", None)

        # check if the modifier is called with a valid working copy
        # with annotations
        if obj is None or obj_annotations is None or repo_annotations is None:
            return [], [], {}

        for annotation_key in self.PRESERVE_ANNOTATION_KEYS:
            obj_val = obj_annotations.get(annotation_key, _marker)
            if obj_val is not _marker:
                # overwrite it with a copy from the working copy, need
                # to deep-copy so that it's not part of the
                # transaction
                repo_annotations[annotation_key] = copy(obj_val)

        return [], [], {}


class OMBaseModifier(RetainAttributeAnnotationItemsBase):
    """Base class for ObjectManager modifiers."""

    PRESERVE_ANNOTATION_KEYS = (DefaultOrdering.ORDER_KEY, DefaultOrdering.POS_KEY)

    def _getOnCloneModifiers(self, obj):
        """Removes all childrens and returns them as references."""
        portal_archivist = getToolByName(obj, "portal_archivist")
        VersionAwareReference = portal_archivist.classes.VersionAwareReference

        # do not pickle the object managers subobjects
        refs = {}
        result_refs = []
        for sub in obj.objectValues():
            result_refs.append(sub)
            refs[id(aq_base(sub))] = True

        def persistent_id(obj):
            try:
                # return a non None value if it is one of the object
                # managers subobjects or raise an KeyError exception
                return refs[id(obj)]
            except KeyError:
                # signalize the pickler to just pickle the 'obj' as
                # usual
                return None

        def persistent_load(ignored):
            return VersionAwareReference()

        return persistent_id, persistent_load, result_refs

    def _beforeSaveModifier(self, obj, clone):
        """Returns all unititialized 'IVersionAwareReference' objects."""
        portal_archivist = getToolByName(obj, "portal_archivist")
        adapter = portal_archivist.classes.ObjectManagerStorageAdapter

        # just return adapters to the attributes that were replaced by
        # a uninitialzed 'IVersionAwareReference' object
        result_refs = []
        for name in clone.objectIds():
            result_refs.append(adapter(clone, name, type="Folder"))

        return result_refs

    def _getAttributeNamesHandlingSubObjects(self, obj, repo_clone):
        attrs = list(set(tuple(repo_clone.objectIds()) + tuple(obj.objectIds())))

        if isinstance(obj, BTreeFolder2Base):
            attrs.extend(["_tree", "_count", "_mt_index"])
        elif isinstance(obj, ObjectManager):
            attrs.extend(["_objects"])

        return attrs


@implementer(ICloneModifier, ISaveRetrieveModifier)
class OMOutsideChildrensModifier(OMBaseModifier):
    """ObjectManager modifier treating all childrens as outside refs

    Treats all childrens as outside references (the repository layer
    knows what to do with that fact).
    """

    def getOnCloneModifiers(self, obj):
        """Removes all childrens and returns them as references."""
        pers_id, pers_load, outside_refs = self._getOnCloneModifiers(obj)
        return pers_id, pers_load, [], outside_refs, ""

    def beforeSaveModifier(self, obj, clone):
        """Returns all unititialized 'IVersionAwareReference' objects.

        This allways goes in conjunction with 'getOnCloneModifiers'.
        """
        outside_refs = self._beforeSaveModifier(obj, clone)
        return {}, [], outside_refs

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        portal_archivist = getToolByName(obj, "portal_archivist")
        OMStorageAdapter = portal_archivist.classes.ObjectManagerStorageAdapter

        ref_names = self._getAttributeNamesHandlingSubObjects(obj, repo_clone)

        # Add objects that have been added to the working copy
        clone_ids = repo_clone.objectIds()
        orig_ids = obj.objectIds()

        for attr_name in orig_ids:
            if attr_name not in clone_ids:
                new_ob = getattr(obj, attr_name, None)
                if new_ob is not None:
                    adapter = OMStorageAdapter(repo_clone, attr_name)
                    adapter.setAttribute(new_ob)

        # Delete references that are no longer relevant
        for attr_name in clone_ids:
            if attr_name not in orig_ids:
                try:
                    repo_clone._delOb(attr_name)
                except AttributeError:
                    pass

        for attr_name in ref_names:
            orig_objects = getattr(obj, attr_name, _marker)
            if orig_objects is not _marker:
                setattr(repo_clone, attr_name, orig_objects)

        RetainAttributeAnnotationItemsBase.afterRetrieveModifier(
            self, obj, repo_clone, preserve
        )

        return [], ref_names, {}


InitializeClass(OMOutsideChildrensModifier)


@implementer(ICloneModifier, ISaveRetrieveModifier)
class OMInsideChildrensModifier(OMBaseModifier):
    """ObjectManager modifier treating all childrens as inside refs

    Treats all childrens as inside references (the repository layer
    knows what to do with that fact).
    """

    def getOnCloneModifiers(self, obj):
        """Removes all childrens and returns them as references."""
        pers_id, pers_load, inside_refs = self._getOnCloneModifiers(obj)
        return pers_id, pers_load, inside_refs, [], ""

    def beforeSaveModifier(self, obj, clone):
        """Returns all unititialized 'IVersionAwareReference' objects.

        This allways goes in conjunction with 'getOnCloneModifiers'.
        """
        inside_refs = self._beforeSaveModifier(obj, clone)
        return {}, inside_refs, []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        hidhandler = getToolByName(obj, "portal_historyidhandler")
        queryUid = hidhandler.queryUid

        # Inside refs from the original object that have no counterpart
        # in the repositories clone have to be deleted from the original.
        # The following steps have to be carried out:
        #
        # 1. list all inside references of the original
        # 2. remove from the list the inside references that just will be
        #    reverted from the repository
        # 3. Return the remaining inside objects that have to be removed
        #    from the original.

        # (1) list originals inside references
        orig_histids = {}
        for id, o in obj.objectItems():
            histid = queryUid(o, None)
            # there may be objects without history_id
            # We want to make sure to delete these on revert
            if histid is not None:
                orig_histids[histid] = id
            else:
                orig_histids["no_history" + id] = id

        # (2) evaluate the refs that get replaced anyway
        for varef in repo_clone.objectValues():
            histid = varef.history_id
            if histid in orig_histids:
                del orig_histids[histid]

        # (3) build the list of adapters to the references to be removed
        refs_to_be_deleted = [
            OMSubObjectAdapter(obj, name) for name in orig_histids.values()
        ]

        # return all attribute names that have something to do with
        # referencing
        ref_names = self._getAttributeNamesHandlingSubObjects(obj, repo_clone)

        # We copy the ordering annotations from the working copy to
        # the repo clone, so that we don't have inconsistencies between the
        # objectValues and objectIds.
        RetainAttributeAnnotationItemsBase.afterRetrieveModifier(self, obj, repo_clone)

        return refs_to_be_deleted, ref_names, {}


InitializeClass(OMInsideChildrensModifier)


@implementer(IReferenceAdapter)
class OMSubObjectAdapter:
    """Adapter to an object manager children."""

    def __init__(self, obj, name):
        """Initialize the adapter."""
        self._obj = obj
        self._name = name

    def save(self, dict):
        """See interface"""
        dict[self._name] = self._obj._getOb(self._name)

    def remove(self, permanent=False):
        """See interface"""
        # XXX do we want there is the ``manage_afterDelete`` hook called?
        # The decision has to go into the interface documentation.
        # IM(alecm)O, we should update the catalog if the change is permanent
        # and not if otherwise, this forces this Adapter to know a bit about
        # implementation details, but it's an optional arg to a specific
        # implemetnation of this interface, so I think this is acceptable.
        # The only other option I see is to do the deletion in the
        # CopyModifyMerge tool which is aware of the distinction between
        # retrieve and revert.
        if permanent:
            self._obj._delObject(self._name)
        else:
            self._obj._delObject(self._name, suppress_events=True)


@implementer(ISaveRetrieveModifier)
class RetainWorkflowStateAndHistory:
    """Standard modifier retaining the working copies workflow state

    Avoids the objects workflow state from beeing retrieved also.
    """

    def beforeSaveModifier(self, obj, clone):
        # Saving the ``review_state`` as this is hard to achieve at retreive
        # (or because I'm dumb). What happened is that ``getInfoFor`` always
        # returned the state of the working copy although the retrieved
        # temporary object was passed to it.
        #
        # Anyway the review state may be a very interesting piece of
        # information for a hypothetic purge policy ...
        wflow = getToolByName(obj, "portal_workflow", None)
        if wflow is not None:
            review_state = wflow.getInfoFor(obj, "review_state", None)
        else:
            review_state = None

        return {"review_state": review_state}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        # replace the workflow stuff of the repository clone by the
        # one of the working copy or delete it
        if getattr(aq_base(obj), "review_state", _marker) is not _marker:
            repo_clone.review_state = obj.review_state
        elif getattr(aq_base(repo_clone), "review_state", _marker) is not _marker:
            del repo_clone.review_state

        if getattr(aq_base(obj), "workflow_history", _marker) is not _marker:
            repo_clone.workflow_history = obj.workflow_history
        elif getattr(aq_base(repo_clone), "workflow_history", _marker) is not _marker:
            del repo_clone.workflow_history

        return [], [], {}


InitializeClass(RetainWorkflowStateAndHistory)


@implementer(ISaveRetrieveModifier)
class RetainPermissionsSettings:
    """Standard modifier retaining permissions settings

    This is nearly essential if we are going to be retaining workflow.
    """

    def beforeSaveModifier(self, obj, clone):
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        # replace the permission stuff of the repository clone by the
        # one of the working copy or delete it
        for key, val in obj.__dict__.items():
            # Find permission settings
            if key.startswith("_") and key.endswith("_Permission"):
                setattr(repo_clone, key, val)

        return [], [], {}


InitializeClass(RetainPermissionsSettings)


@implementer(ISaveRetrieveModifier)
class RetainUIDs:
    """Modifier which ensures uid consistency by retaining the uid from the working copy.  Ensuring
    that newly created objects are assigned an appropriate uid is a job for the repository tool.
    """

    def beforeSaveModifier(self, obj, clone):
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        # Preserve CMFUid
        uid_tool = getToolByName(obj, "portal_historyidhandler", None)
        if uid_tool is not None:
            working_uid = uid_tool.queryUid(obj)
            anno_tool = getToolByName(obj, "portal_uidannotation")
            annotation = anno_tool(repo_clone, uid_tool.UID_ATTRIBUTE_NAME)
            annotation.setUid(working_uid)

        return [], [], {}


InitializeClass(RetainUIDs)


@implementer(IAttributeModifier)
class SaveFileDataInFileTypeByReference:
    """Standard modifier avoiding unnecessary cloning of the file data.

    Called on 'Portal File' objects.
    """

    def getReferencedAttributes(self, obj):
        return {"data": getattr(aq_base(obj), "data", None)}

    def reattachReferencedAttributes(self, obj, attrs_dict):

        obj = aq_base(obj)
        for name, attr_value in attrs_dict.items():
            setattr(obj, name, attr_value)


InitializeClass(SaveFileDataInFileTypeByReference)


@implementer(ICloneModifier, ISaveRetrieveModifier)
class SkipParentPointers:
    """Standard modifier to avoid cloning of __parent__ pointers and
    restore them from context
    """

    def getOnCloneModifiers(self, obj):
        """Removes parent pointers and stores a marker"""
        parent = getattr(obj, "__parent__", _marker)
        if parent is _marker:
            return None

        parent_id = id(aq_base(parent))

        def persistent_id(obj):
            if id(aq_base(obj)) == parent_id:
                return True
            return None

        def persistent_load(obj):
            # Set the value to None on clone
            return None

        return persistent_id, persistent_load, [], []

    def beforeSaveModifier(self, obj, clone):
        """Does nothing, the pickler does the work"""
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        """Install the parent from the working copy"""
        if (
            getattr(repo_clone, "__parent__", _marker) is None
            and getattr(obj, "__parent__", _marker) is not _marker
        ):
            repo_clone.__parent__ = obj.__parent__
        return [], [], {}


InitializeClass(SkipParentPointers)


@implementer(ICloneModifier, ISaveRetrieveModifier)
class SkipRegistryBasesPointers:
    """Standard modifier to avoid cloning of component registry
    __bases__ and restore them from context
    """

    def querySiteManager(self, obj):
        if not IPossibleSite.providedBy(obj):
            return
        try:
            registry = obj.getSiteManager()
        except ComponentLookupError:
            return
        return registry

    def getOnCloneModifiers(self, obj):
        """Removes component registry bases pointers and stores a marker"""
        registry = self.querySiteManager(obj)
        if registry is None:
            return

        component_bases = dict(
            registry={id(aq_base(base)): aq_base(base) for base in registry.__bases__},
            utilities={
                id(aq_base(base)): aq_base(base)
                for base in registry.utilities.__bases__
            },
            adapters={
                id(aq_base(base)): aq_base(base) for base in registry.adapters.__bases__
            },
        )

        def persistent_id(obj):
            obj_id = id(aq_base(obj))
            for key, bases in component_bases.items():
                if obj_id in bases:
                    return f"{key}:{obj_id}"
            return None

        def persistent_load(obj):
            key, base_id = obj.split(":")
            return component_bases[key][int(base_id)]

        return persistent_id, persistent_load, [], []

    def beforeSaveModifier(self, obj, clone):
        """Don't save the bases."""
        sm = self.querySiteManager(clone)
        if sm is not None:
            sm.__bases__ = ()
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        """Does nothing, the pickler does the work"""
        sm = self.querySiteManager(repo_clone)
        if sm is not None and obj is not None:
            obj_sm = obj.getSiteManager()
            sm.__bases__ = obj_sm.__bases__
        return [], [], {}


InitializeClass(SkipRegistryBasesPointers)


@implementer(ISaveRetrieveModifier)
class SillyDemoRetrieveModifier:
    """Silly Retrieve Modifier for Demos

    Disabled by default and if enabled only effective if the
    username is ``gregweb``.

    This is really just as silly example though for demo purposes!!!
    """

    def beforeSaveModifier(self, obj, clone):
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        from AccessControl import getSecurityManager

        if getSecurityManager().getUser().getUserName() != "gregweb":
            return [], [], {}

        if repo_clone.portal_type != "Document":
            return [], [], {}

        # sorry: hack
        clone = repo_clone.__of__(obj.aq_inner.aq_parent)

        # replace all occurences of DeMo with Demo and deMo with demo
        text = clone.EditableBody()
        text = text.replace("DeMo", "Demo").replace("deMo", "demo")
        clone.setText(text)

        return [], [], {}


InitializeClass(SillyDemoRetrieveModifier)


@implementer(IConditionalTalesModifier, ICloneModifier)
class AbortVersioningOfLargeFilesAndImages(ConditionalTalesModifier):
    """Raises an error if a file or image attribute stored on the
    object in a specified field is larger than a fixed default"""

    field_names = ("file", "image")
    max_size = 26214400  # This represents a 400 element long Pdata list

    modifierEditForm = PageTemplateFile(
        "www/fieldModifierEditForm.pt", globals(), __name__="modifierEditForm"
    )

    _condition = Expression("python: portal_type in ('Image', 'File')")

    def __init__(
        self, id="AbortVersioningOfLargeFilesAndImages", modifier=None, title=""
    ):
        self.id = str(id)
        self.title = str(title)
        self.meta_type = "edmod_%s" % id
        self._enabled = False

    def edit(
        self,
        enabled=None,
        condition=None,
        title="",
        field_names=None,
        max_size=None,
        REQUEST=None,
    ):
        """See IConditionalTalesModifier."""
        if max_size is not None:
            self.max_size = int(max_size)
        if field_names is not None:
            field_names = tuple(s.strip() for s in field_names.split("\n") if s)
            if field_names != self.field_names:
                self.field_names = field_names
        return ConditionalTalesModifier.edit(self, enabled, condition, title)

    def getFieldNames(self):
        """For the edit form"""
        return "\n".join(self.field_names)

    def getModifier(self):
        """We are the modifier, not some silly wrapper."""
        return self

    def _getFieldValues(self, obj):
        """Finds the specified field values and returns them if
        they contain file objects which are too large.  Specifically,
        it returns an iterator of tuples containing the type of storage,
        the field name, and the value stored.

        The type of storage is currently always 'attribute'.
        We used to also have 'annotation', but that was only for
        fields stored via Archetypes AnnotationStorage.
        """
        max_size = self.max_size

        # Search for fields stored via AttributeStorage
        for name in self.field_names:
            val = getattr(obj, name, None)
            # Skip linked Pdata chains too long for the pickler
            if hasattr(aq_base(val), "getSize") and callable(val.getSize):
                size = val.getSize()
                if isinstance(size, int) and size >= max_size:
                    yield "attribute", name, val

    def getOnCloneModifiers(self, obj):
        """Detects large file objects and raises an error"""
        for storage, name, val in self._getFieldValues(obj):
            # if we find a file that's too big, abort
            raise FileTooLargeToVersionError
        return None  # no effect otherwise


InitializeClass(AbortVersioningOfLargeFilesAndImages)

_empty_marker = []


class LargeFilePlaceHolder:
    """PlaceHolder for a large object"""

    @staticmethod
    def getSize():
        return sys.maxsize


@implementer(IConditionalTalesModifier, ICloneModifier, ISaveRetrieveModifier)
class SkipVersioningOfLargeFilesAndImages(AbortVersioningOfLargeFilesAndImages):
    """Replaces any excessively large file and images stored as
    annotations or attributes on the object with a marker.  On
    retrieve, the marker will be replaced with the current value.."""

    def getOnCloneModifiers(self, obj):
        """Removes large file objects and returns them as references"""
        refs = {}
        ref_list = []
        for storage, name, val in self._getFieldValues(obj):
            ref_list.append(val)
            refs[id(val)] = True

        if not refs:
            return None  # don't do anything

        def persistent_id(obj):
            return refs.get(id(obj), None)

        def persistent_load(ignored):
            return LargeFilePlaceHolder()

        return persistent_id, persistent_load, [], []

    def beforeSaveModifier(self, obj, clone):
        """Does nothing, the pickler does the work"""
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        """If we find any LargeFilePlaceHolders, replace them with the
        values from the current working copy.  If the values are missing
        from the working copy, remove them from the retrieved object."""
        for storage, name, orig_val in self._getFieldValues(repo_clone):
            if isinstance(orig_val, LargeFilePlaceHolder):
                # attribute storage
                val = getattr(obj, name, _empty_marker)
                if val is not _empty_marker:
                    setattr(repo_clone, name, val)
                else:
                    delattr(repo_clone, name)
        return [], [], {}


InitializeClass(SkipVersioningOfLargeFilesAndImages)


@implementer(ICloneModifier, ISaveRetrieveModifier)
class Skip_z3c_blobfile:
    """Standard avoid storing blob data, may be useful for extremely
    large files where versioing the non-file metadata is important but
    the cost of versioning the file data is too high.
    """

    def _blob_file_classes(self):
        blob_file_classes = []
        try:
            from z3c.blobfile.file import File
        except ImportError:
            pass
        else:
            blob_file_classes.append(File)
        try:
            from plone.namedfile.file import NamedBlobFile
        except ImportError:
            pass
        else:
            blob_file_classes.append(NamedBlobFile)
        return tuple(blob_file_classes)

    def getOnCloneModifiers(self, obj):
        """Removes z3c.blobfile fields"""
        blob_file_classes = self._blob_file_classes()
        if not blob_file_classes:
            return

        blob_refs = {
            id(v) for v in obj.__dict__.values() if isinstance(v, blob_file_classes)
        }

        def persistent_id(obj):
            if id(aq_base(obj)) in blob_refs:
                return True
            return None

        def persistent_load(ignored):
            return None

        return persistent_id, persistent_load, [], []

    def beforeSaveModifier(self, obj, clone):
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        blob_file_classes = self._blob_file_classes()
        if not blob_file_classes:
            return [], [], {}

        if obj is None:
            return [], [], {}

        blob_fields = (
            (k, v) for k, v in obj.__dict__.items() if isinstance(v, blob_file_classes)
        )

        for k, v in blob_fields:
            setattr(repo_clone, k, v)

        return [], [], {}


InitializeClass(Skip_z3c_blobfile)

# ----------------------------------------------------------------------
# Standard modifier configuration
# ----------------------------------------------------------------------

modifiers = (
    {
        "id": "OMInsideChildrensModifier",
        "title": "Modifier for object managers treating children as inside objects.",
        "enabled": True,
        "condition": 'python: object and path("object/isPrincipiaFolderish|nothing") and not path("object/@@plone/isStructuralFolder|nothing")',
        "wrapper": ConditionalTalesModifier,
        "modifier": OMInsideChildrensModifier,
        "form": manage_OMInsideChildrensModifierAddForm,
        "factory": manage_addOMInsideChildrensModifier,
        "icon": "www/modifier.gif",
    },
    {
        "id": "OMOutsideChildrensModifier",
        "title": "Modifier for object managers (like standard folders) treating children as outside objects.",
        "enabled": True,
        "condition": "python:path('object/@@plone/isStructuralFolder|nothing') or portal_type == 'Folder'",
        "wrapper": ConditionalTalesModifier,
        "modifier": OMOutsideChildrensModifier,
        "form": manage_OMOutsideChildrensModifierAddForm,
        "factory": manage_addOMOutsideChildrensModifier,
        "icon": "www/modifier.gif",
    },
    {
        "id": "RetainUIDs",
        "title": "Retains the CMF UIDs from the working copy",
        "enabled": True,
        "wrapper": ConditionalModifier,
        "modifier": RetainUIDs,
        "form": manage_RetainUIDsModifierAddForm,
        "factory": manage_addRetainUIDs,
        "icon": "www/modifier.gif",
    },
    {
        "id": "RetainWorkflowStateAndHistory",
        "title": "Retains the working copies workflow state upon retrieval/revertion.",
        "enabled": True,
        "wrapper": ConditionalModifier,
        "modifier": RetainWorkflowStateAndHistory,
        "form": manage_RetainWorkflowStateAndHistoryModifierAddForm,
        "factory": manage_addRetainWorkflowStateAndHistory,
        "icon": "www/modifier.gif",
    },
    {
        "id": "RetainPermissionsSettings",
        "title": "Retains the permission settings upon retrieval/revertion.",
        "enabled": True,
        "wrapper": ConditionalModifier,
        "modifier": RetainPermissionsSettings,
        "form": manage_RetainPermissionsSettingsAddForm,
        "factory": manage_addRetainPermissionsSettings,
        "icon": "www/modifier.gif",
    },
    {
        "id": "SaveFileDataInFileTypeByReference",
        "title": "Let's the storage optimize cloning of file data.",
        "enabled": False,
        "condition": "python: meta_type=='Portal File'",
        "wrapper": ConditionalTalesModifier,
        "modifier": SaveFileDataInFileTypeByReference,
        "form": manage_SaveFileDataInFileTypeByReferenceModifierAddForm,
        "factory": manage_addSaveFileDataInFileTypeByReference,
        "icon": "www/modifier.gif",
    },
    {
        "id": "SillyDemoRetrieveModifier",
        "title": "Silly retrive modifier for demos only.",
        "enabled": False,
        "condition": "python: True",
        "wrapper": ConditionalTalesModifier,
        "modifier": SillyDemoRetrieveModifier,
        "form": manage_SillyDemoRetrieveModifierAddForm,
        "factory": manage_addSillyDemoRetrieveModifier,
        "icon": "www/modifier.gif",
    },
    {
        "id": "SkipParentPointers",
        "title": "Skip Saving of Parent Pointers",
        "enabled": True,
        "condition": "python: True",
        "wrapper": ConditionalTalesModifier,
        "modifier": SkipParentPointers,
        "form": manage_SkipParentPointersAddForm,
        "factory": manage_addSkipParentPointers,
        "icon": "www/modifier.gif",
    },
    {
        "id": "SkipRegistryBasesPointers",
        "title": "Skip Saving of Component Registry Bases",
        "enabled": True,
        "condition": "python: True",
        "wrapper": ConditionalTalesModifier,
        "modifier": SkipRegistryBasesPointers,
        "form": manage_SkipRegistryBasesPointersAddForm,
        "factory": manage_addSkipRegistryBasesPointers,
        "icon": "www/modifier.gif",
    },
    {
        "id": "AbortVersioningOfLargeFilesAndImages",
        "title": "Abort versioning of objects if file data if it's too large",
        "enabled": True,
        "condition": "python: portal_type in ('Image', 'File')",
        "wrapper": AbortVersioningOfLargeFilesAndImages,
        "modifier": AbortVersioningOfLargeFilesAndImages,
        "form": manage_AbortVersioningOfLargeFilesAndImagesAddForm,
        "factory": manage_addAbortVersioningOfLargeFilesAndImages,
        "icon": "www/modifier.gif",
    },
    {
        "id": "SkipVersioningOfLargeFilesAndImages",
        "title": "Skip versioning of objects if file data if it's too large",
        "enabled": False,
        "condition": "python: portal_type in ('Image', 'File')",
        "wrapper": SkipVersioningOfLargeFilesAndImages,
        "modifier": SkipVersioningOfLargeFilesAndImages,
        "form": manage_SkipVersioningOfLargeFilesAndImagesAddForm,
        "factory": manage_addSkipVersioningOfLargeFilesAndImages,
        "icon": "www/modifier.gif",
    },
    {
        "id": "Skip_z3c_blobfile",
        "title": "Skip storing z3c.blobfile.file.File fields on objects",
        "enabled": True,
        "condition": "python:True",
        "wrapper": ConditionalTalesModifier,
        "modifier": Skip_z3c_blobfile,
        "form": manage_Skip_z3c_blobfileAddForm,
        "factory": manage_addSkip_z3c_blobfile,
        "icon": "www/modifier.gif",
    },
)
