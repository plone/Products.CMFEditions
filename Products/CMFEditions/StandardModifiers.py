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

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import ManagePortal

from Products.CMFEditions.interfaces.IModifier import IAttributeModifier
from Products.CMFEditions.interfaces.IModifier import ICloneModifier
from Products.CMFEditions.interfaces.IModifier import ISaveRetrieveModifier
from Products.CMFEditions.interfaces.IModifier import IConditionalTalesModifier
from Products.CMFEditions.Modifiers import ConditionalModifier
from Products.CMFEditions.Modifiers import ConditionalTalesModifier
from Products.CMFEditions.Modifiers import manage_addModifierForm
from Products.CMFEditions.Modifiers import manage_addTalesModifierForm

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
        title = m['title']
        modifier = m['modifier']()
        wrapper = m['wrapper'](id, modifier, title)
        enabled = m['enabled']
        if IConditionalTalesModifier.isImplementedBy(wrapper):
            wrapper.edit(enabled, m['condition'])
        else:
            wrapper.edit(enabled)

        portal_modifier.register(m['id'], wrapper)

def manage_addOMOutsideChildrensModifier(self, id, title=None, REQUEST=None):
    """Add an object manager modifier treating childrens as outside refs
    """
    modifier = OMOutsideChildrensModifier()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

def manage_addOMInsideChildrensModifier(self, id, title=None,
                                        REQUEST=None):
    """Add an object manager modifier treating children as inside refs
    """
    modifier = OMInsideChildrensModifier()
    self._setObject(id, ConditionalTalesModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

def manage_addRetainWorkflowStateAndHistory(self, id, title=None,
                                            REQUEST=None):
    """Add a modifier retaining workflow state upon retrieve.
    """
    modifier = RetainWorkflowStateAndHistory()
    self._setObject(id, ConditionalModifier(id, modifier, title))

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

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
            result_refs.append(AttributeAdapter(clone, name))

        return result_refs


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

    def afterRetrieveModifier(self, obj, repo_clone):
        return {}

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
        hidhandler = getToolByName(target_obj, 'portal_historyidhandler')
        queryUid = hidhandler.queryUid

        # Inside refs from the original object that have no corresponding
        # in the repositories clone have to be deleted from the original.
        # The following steps have to be carried out:
        # 
        # 1. list all inside references of the original
        # 2. remove from the list the inside references that just will be 
        #    received
        # 3. Remove the remaining inside objects from the original.
        
        # (1) list originals inside references
        orig_histids = {}
        for id, o in obj.objectItems():
            histid = queryUid(o, None)
            orig_histids[histid] = id
        # there may be objects without 
        if None in orig_histids:
            del orig_histids[None]
        
        # (2) evaluate the refs that get replaces anyway
        for varef in repo_clone.objectValues():
            histid = varef.history_id
            if histid in orig_histids:
                del orig_histids[histid]
        
        # (3) remove: XXX arghh, we can't do this here
        obj.manage_delObjects(ids=orig_histid.values())
        
        return {}


InitializeClass(OMOutsideChildrensModifier)

_marker = []

class RetainWorkflowStateAndHistory:
    """Standard modifier retaining the working copies workflow state

    Avoids the objects workflow state from beeing retrieved also.
    """

    __implements__ = (ISaveRetrieveModifier, )

    def beforeSaveModifier(self, obj, clone):
        return [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=[]):
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

        return {}

InitializeClass(RetainWorkflowStateAndHistory)


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
        'form': manage_addTalesModifierForm,
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
        'form': manage_addTalesModifierForm,
        'factory': manage_addOMOutsideChildrensModifier,
        'icon': 'www/modifier.gif',
    },
    {
        'id': 'RetainWorkflowStateAndHistory',
        'title': "Retains the working copies workflow state upon retrieval/revertion.",
        'enabled': True,
        'wrapper': ConditionalModifier,
        'modifier': RetainWorkflowStateAndHistory,
        'form': manage_addModifierForm,
        'factory': manage_addRetainWorkflowStateAndHistory,
        'icon': 'www/modifier.gif',
    },
    {
        'id': 'SaveFileDataInFileTypeByReference',
        'title': "Let's the storage optimize cloning of file data.",
        'enabled': True,
        'condition': "python: meta_type=='Portal File'",
        'wrapper': ConditionalTalesModifier,
        'modifier': SaveFileDataInFileTypeByReference,
        'form': manage_addTalesModifierForm,
        'factory': manage_addSaveFileDataInFileTypeByReference,
        'icon': 'www/modifier.gif',
    },
)
