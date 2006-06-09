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

$Id: StandardModifiers.py,v 1.13 2005/06/26 13:28:36 gregweb Exp $
"""

from Persistence import Persistent
from Globals import InitializeClass

from Acquisition import aq_base

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import ManagePortal

from Products.CMFEditions.interfaces.IModifier import IAttributeModifier
from Products.CMFEditions.interfaces.IModifier import ICloneModifier
from Products.CMFEditions.interfaces.IModifier import ISaveRetrieveModifier
from Products.CMFEditions.interfaces.IModifier import IConditionalTalesModifier
from Products.CMFEditions.interfaces.IModifier import IReferenceAdapter
from Products.CMFEditions.Modifiers import ConditionalModifier
from Products.CMFEditions.Modifiers import ConditionalTalesModifier

try:
    from Products.Archetypes.config import UUID_ATTR, REFERENCE_ANNOTATION
except ImportError:
    UUID_ATTR = None
    REFERENCE_ANNOTATION
    
#----------------------------------------------------------------------
# Product initialziation, installation and factory stuff
#----------------------------------------------------------------------

def initialize(context):
    """Registers modifiers with zope (on zope startup).
    """
    for m in modifiers:
        context.registerClass(
            m['wrapper'], m['id'],
            permission = ManagePortal,
            constructors = (m['form'], m['factory']),
            icon = m['icon'],
        )

def install(portal_modifier):
    """Registers modifiers in the modifier registry (at tool install time).
    """
    for m in modifiers:
        id = m['id']
        if id in portal_modifier.objectIds():
            continue
        title = m['title']
        modifier = m['modifier']()
        wrapper = m['wrapper'](id, modifier, title)
        enabled = m['enabled']
        if IConditionalTalesModifier.isImplementedBy(wrapper):
            wrapper.edit(enabled, m['condition'])
        else:
            wrapper.edit(enabled)

        portal_modifier.register(m['id'], wrapper)


manage_OMOutsideChildrensModifierAddForm = PageTemplateFile('www/OMOutsideChildrensModifierAddForm.pt',
                                          globals(),
                                          __name__='manage_OMOutsideChildrensModifierAddForm')

def manage_addOMOutsideChildrensModifier(self, id, title=None, REQUEST=None):
    """Add an object manager modifier treating childrens as outside refs
    """
    modifier = OMOutsideChildrensModifier()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


manage_OMInsideChildrensModifierAddForm = PageTemplateFile('www/OMInsideChildrensModifierAddForm.pt',
                                          globals(),
                                          __name__='manage_OMInsideChildrensModifierAddForm')

def manage_addOMInsideChildrensModifier(self, id, title=None,
                                        REQUEST=None):
    """Add an object manager modifier treating children as inside refs
    """
    modifier = OMInsideChildrensModifier()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


manage_RetainUIDsModifierAddForm =  \
                         PageTemplateFile('www/RetainUIDsModifierAddForm.pt',
                                          globals(),
                                          __name__='manage_RetainUIDsModifierAddForm')

def manage_addRetainUIDs(self, id, title=None, REQUEST=None):
    """Add a modifier retaining UIDs upon retrieve.
    """
    modifier = RetainUIDs()
    self._setObject(id, ConditionalModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


manage_RetainATRefsModifierAddForm =  \
               PageTemplateFile('www/RetainATRefsModifierAddForm.pt',
                                globals(),
                                __name__='manage_RetainUIDsModifierAddForm')

def manage_addRetainATRefs(self, id, title=None, REQUEST=None):
    """Add a modifier retaining AT References upon retrieve.
    """
    modifier = RetainATRefs()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


manage_RetainWorkflowStateAndHistoryModifierAddForm =  \
                         PageTemplateFile('www/RetainWorkflowStateAndHistoryModifierAddForm.pt',
                                          globals(),
                                          __name__='manage_RetainWorkflowStateAndHistoryModifierAddForm')

def manage_addRetainWorkflowStateAndHistory(self, id, title=None,
                                            REQUEST=None):
    """Add a modifier retaining workflow state upon retrieve.
    """
    modifier = RetainWorkflowStateAndHistory()
    self._setObject(id, ConditionalModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


manage_RetainPermissionsSettingsAddForm =  \
                         PageTemplateFile('www/RetainPermissionsSettingsModifierAddForm.pt',
                                          globals(),
                                          __name__='manage_RetainPermissionsSettingsModifierAddForm')

def manage_addRetainPermissionsSettings(self, id, title=None,
                                            REQUEST=None):
    """Add a modifier retaining permissions upon retrieve.
    """
    modifier = RetainPermissionsSettings()
    self._setObject(id, ConditionalModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


manage_SaveFileDataInFileTypeByReferenceModifierAddForm =  \
                         PageTemplateFile('www/SaveFileDataInFileTypeByReferenceModifierAddForm.pt',
                                          globals(),
                                          __name__='manage_SaveFileDataInFileTypeByReferenceModifierAddForm')

def manage_addSaveFileDataInFileTypeByReference(self, id, title=None,
                                                REQUEST=None):
    """Add a modifier avoiding unnecessary cloning of file data.
    """
    modifier = SaveFileDataInFileTypeByReference()
    self._setObject(id, ConditionalModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


#----------------------------------------------------------------------
# Standard modifier implementation
#----------------------------------------------------------------------

class OMBaseModifier:
    """Base class for ObjectManager modifiers.
    """

    def _getOnCloneModifiers(self, obj):
        """Removes all childrens and returns them as references.
        """
        portal_archivist = getToolByName(obj, 'portal_archivist')
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
        """Returns all unititialized 'IVersionAwareReference' objects.
        """
        portal_archivist = getToolByName(obj, 'portal_archivist')
        AttributeAdapter = portal_archivist.classes.AttributeAdapter

        # just return adapters to the attributes that were replaced by
        # a uninitialzed 'IVersionAwareReference' object
        result_refs = []
        for name in clone.objectIds():
            result_refs.append(AttributeAdapter(clone, name, type="ObjectManager"))

        return result_refs

    def _getAttributeNamesHandlingSubObjects(self, obj, repo_clone):
        attrs = ['_objects']
        attrs.extend(repo_clone.objectIds())
        attrs.extend(obj.objectIds())
        return attrs

class OMOutsideChildrensModifier(OMBaseModifier):
    """ObjectManager modifier treating all childrens as outside refs

    Treats all childrens as outside references (the repository layer
    knows what to do with that fact).
    """

    __implements__ = (ICloneModifier, ISaveRetrieveModifier)

    def getOnCloneModifiers(self, obj):
        """Removes all childrens and returns them as references.
        """
        pers_id, pers_load, outside_refs = self._getOnCloneModifiers(obj)
        return pers_id, pers_load, [], outside_refs, ''

    def beforeSaveModifier(self, obj, clone):
        """Returns all unititialized 'IVersionAwareReference' objects.

        This allways goes in conjunction with 'getOnCloneModifiers'.
        """
        outside_refs = self._beforeSaveModifier(obj, clone)
        return [], outside_refs

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        ref_names = self._getAttributeNamesHandlingSubObjects(obj, repo_clone)

        # Add objects that have been added to the working copy
        clone_ids = repo_clone.objectIds()
        orig_ids = obj.objectIds()
        for attr_name in orig_ids:
            if attr_name not in clone_ids:
                new_ob = getattr(obj, attr_name, None)
                if new_ob is not None:
                    repo_clone._setOb(attr_name, new_ob)

        # Delete references that are no longer relevant
        for attr_name in clone_ids:
            if attr_name not in orig_ids:
                try:
                    repo_clone._delOb(attr_name)
                except AttributeError:
                    pass

        # Restore _objects, so that order is preserved and ids are consistent
        orig_objects = getattr(obj, '_objects', None)
        if orig_objects is not None:
            repo_clone._objects = orig_objects

        return [], ref_names, {}

InitializeClass(OMOutsideChildrensModifier)


class OMInsideChildrensModifier(OMBaseModifier):
    """ObjectManager modifier treating all childrens as inside refs

    Treats all childrens as inside references (the repository layer
    knows what to do with that fact).
    """

    __implements__ = (ICloneModifier, ISaveRetrieveModifier)

    def getOnCloneModifiers(self, obj):
        """Removes all childrens and returns them as references.
        """
        pers_id, pers_load, inside_refs = self._getOnCloneModifiers(obj)
        return pers_id, pers_load, inside_refs, [], ''

    def beforeSaveModifier(self, obj, clone):
        """Returns all unititialized 'IVersionAwareReference' objects.

        This allways goes in conjunction with 'getOnCloneModifiers'.
        """
        inside_refs = self._beforeSaveModifier(obj, clone)
        return inside_refs, []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        hidhandler = getToolByName(obj, 'portal_historyidhandler')
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
                orig_histids['no_history'+id]=id

        # (2) evaluate the refs that get replaced anyway
        for varef in repo_clone.objectValues():
            histid = varef.history_id
            if histid in orig_histids:
                del orig_histids[histid]

        # (3) build the list of adapters to the references to be removed
        refs_to_be_deleted = \
            [OMSubObjectAdapter(obj, name) for name in orig_histids.values()]

        # return all attribute names that have something to do with
        # referencing
        ref_names = self._getAttributeNamesHandlingSubObjects(obj, repo_clone)
        return refs_to_be_deleted, ref_names, {}

InitializeClass(OMOutsideChildrensModifier)

class OMSubObjectAdapter:
    """Adapter to an object manager children.
    """

    __implements__ = (IReferenceAdapter, )

    def __init__(self, obj, name):
        """Initialize the adapter.
        """
        self._obj = obj
        self._name = name

    def save(self, dict):
        """See interface
        """
        dict[self._name] = getattr(aq_base(self._obj), self._name)

    def remove(self, permanent=False):
        """See interface
        """
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
            self._obj.manage_delObjects(ids=[self._name])
        else:
            self._obj._delOb(self._name)


_marker = []

class RetainWorkflowStateAndHistory:
    """Standard modifier retaining the working copies workflow state

    Avoids the objects workflow state from beeing retrieved also.
    """

    __implements__ = (ISaveRetrieveModifier, )

    def beforeSaveModifier(self, obj, clone):
        return [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        # replace the workflow stuff of the repository clone by the
        # one of the working copy or delete it
        if getattr(aq_base(obj), 'review_state', _marker) is not _marker:
            repo_clone.review_state = obj.review_state
        elif (getattr(aq_base(repo_clone), 'review_state', _marker)
              is not _marker):
            del repo_clone.review_state

        if getattr(aq_base(obj), 'workflow_history', _marker) is not _marker:
            repo_clone.workflow_history = obj.workflow_history
        elif (getattr(aq_base(repo_clone), 'workflow_history', _marker)
              is not _marker):
            del repo_clone.workflow_history

        return [], [], {}

InitializeClass(RetainWorkflowStateAndHistory)

class RetainPermissionsSettings:
    """Standard modifier retaining permissions settings

    This is nearly essential if we are going to be retaining workflow.
    """

    __implements__ = (ISaveRetrieveModifier, )

    def beforeSaveModifier(self, obj, clone):
        return [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        # replace the permission stuff of the repository clone by the
        # one of the working copy or delete it
        for key, val in obj.__dict__.items():
            # Find permission settings
            if key.startswith('_') and key.endswith('_Permission'):
                setattr(repo_clone, key, val)

        return [], [], {}

InitializeClass(RetainPermissionsSettings)

class RetainUIDs:
    """Modifier which ensures uid consistency by retaining the uid from the working copy.  Ensuring
       that newly created objects are assigned an appropriate uid is a job for the repository tool.
    """

    __implements__ = (ISaveRetrieveModifier, )

    def beforeSaveModifier(self, obj, clone):
        return [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        #Preserve CMFUid
        uid_tool = getToolByName(obj, 'portal_historyidhandler', None)
        if uid_tool is not None:
            working_uid = uid_tool.queryUid(obj)
            copy_uid = uid_tool.queryUid(repo_clone)
            anno_tool = getToolByName(obj, 'portal_uidannotation')
            annotation = anno_tool(repo_clone, uid_tool.UID_ATTRIBUTE_NAME)
            annotation.setUid(working_uid)

        #Preserve ATUID
        uid = getattr(aq_base(obj), 'UID', None)
        if UUID_ATTR is not None and uid is not None and callable(obj.UID):
            working_atuid = obj.UID()
            repo_uid = repo_clone.UID()
            setattr(repo_clone, UUID_ATTR, working_atuid)
            if working_atuid != repo_uid:
                # XXX: We need to do something with forward references
                annotations = repo_clone._getReferenceAnnotations()
                for ref in annotations.objectValues():
                    ref.sourceUID = working_atuid

        return [], [], {}

InitializeClass(RetainUIDs)

class RetainATRefs:
    """Modifier which ensures the Archetypes references of the working
       copy are preserved when reverting to a previous version
    """

    __implements__ = (ISaveRetrieveModifier, )

    def beforeSaveModifier(self, obj, clone):
        return [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        # check if the modifier is called with a valid working copy
        if obj is None:
            return [], [], {}

        #Preserve AT references
        orig_refs_container = getattr(aq_base(obj), REFERENCE_ANNOTATION)
        setattr(repo_clone, REFERENCE_ANNOTATION, orig_refs_container)
        return [], [], {}

InitializeClass(RetainATRefs)

class SaveFileDataInFileTypeByReference:
    """Standard modifier avoiding unnecessary cloning of the file data.

    Called on 'Portal File' objects.
    """

    __implements__ = (IAttributeModifier, )

    def getReferencedAttributes(self, obj):
        return {'data': getattr(aq_base(obj),'data', None)}

    def reattachReferencedAttributes(self, obj, attrs_dict):

        obj = aq_base(obj)
        for name, attr_value in attrs_dict.items():
            setattr(obj, name, attr_value)


InitializeClass(SaveFileDataInFileTypeByReference)


#----------------------------------------------------------------------
# Standard modifier configuration
#----------------------------------------------------------------------

modifiers = (
    {
        'id': 'OMInsideChildrensModifier',
        'title': "Modifier for object managers treating children as inside objects.",
        'enabled': False,
        'condition': 'python: False',
        'wrapper': ConditionalTalesModifier,
        'modifier': OMInsideChildrensModifier,
        'form': manage_OMInsideChildrensModifierAddForm,
        'factory': manage_addOMInsideChildrensModifier,
        'icon': 'www/modifier.gif',
    },
    {
        'id': 'OMOutsideChildrensModifier',
        'title': "Modifier for object managers (like standard folders) treating children as outside objects.",
        'enabled': True,
        'condition': "python: portal_type=='Folder'",
        'wrapper': ConditionalTalesModifier,
        'modifier': OMOutsideChildrensModifier,
        'form': manage_OMOutsideChildrensModifierAddForm,
        'factory': manage_addOMOutsideChildrensModifier,
        'icon': 'www/modifier.gif',
    },
    {
        'id': 'RetainUIDs',
        'title': "Retains the CMF and AT UIDs from the working copy",
        'enabled': True,
        'wrapper': ConditionalModifier,
        'modifier': RetainUIDs,
        'form': manage_RetainUIDsModifierAddForm,
        'factory': manage_addRetainUIDs,
        'icon': 'www/modifier.gif',
    },
    {
        'id': 'RetainATRefs',
        'title': "Retains AT refs",
        'enabled': False,
        'condition': 'python: False',
        'wrapper': ConditionalTalesModifier,
        'modifier': RetainATRefs,
        'form': manage_RetainATRefsModifierAddForm,
        'factory': manage_addRetainATRefs,
        'icon': 'www/modifier.gif',
    },
    {
        'id': 'RetainWorkflowStateAndHistory',
        'title': "Retains the working copies workflow state upon retrieval/revertion.",
        'enabled': True,
        'wrapper': ConditionalModifier,
        'modifier': RetainWorkflowStateAndHistory,
        'form': manage_RetainWorkflowStateAndHistoryModifierAddForm,
        'factory': manage_addRetainWorkflowStateAndHistory,
        'icon': 'www/modifier.gif',
    },
    {
        'id': 'RetainPermissionsSettings',
        'title': "Retains the permission settings upon retrieval/revertion.",
        'enabled': True,
        'wrapper': ConditionalModifier,
        'modifier': RetainPermissionsSettings,
        'form': manage_RetainPermissionsSettingsAddForm ,
        'factory': manage_addRetainPermissionsSettings,
        'icon': 'www/modifier.gif',
    },
    {
        'id': 'SaveFileDataInFileTypeByReference',
        'title': "Let's the storage optimize cloning of file data.",
        'enabled': True,
        'condition': "python: meta_type=='Portal File'",
        'wrapper': ConditionalTalesModifier,
        'modifier': SaveFileDataInFileTypeByReference,
        'form': manage_SaveFileDataInFileTypeByReferenceModifierAddForm,
        'factory': manage_addSaveFileDataInFileTypeByReference,
        'icon': 'www/modifier.gif',
    },
)
