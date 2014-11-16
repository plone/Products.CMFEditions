# -*- coding: utf-8 -*-
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
"""Registry of Modifiers

"""

from zope.interface import implements

from App.class_init import InitializeClass
from Missing import MV

from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from OFS.OrderedFolder import OrderedFolder

from Products.CMFCore.utils import UniqueObject, getToolByName

from Products.CMFCore.permissions import ManagePortal

from Products.CMFEditions.utilities import KwAsAttributes

from Products.CMFEditions.interfaces import IPortalModifierTool
from Products.CMFEditions.interfaces.IModifier import IAttributeModifier
from Products.CMFEditions.interfaces.IModifier import ICloneModifier
from Products.CMFEditions.interfaces.IModifier import ISaveRetrieveModifier
from Products.CMFEditions.interfaces.IModifier import IModifierRegistrySet
from Products.CMFEditions.interfaces.IModifier import IModifierRegistryQuery
from Products.CMFEditions.interfaces.IModifier import IConditionalModifier
from Products.CMFEditions.interfaces.IModifier import IConditionalTalesModifier

from Products.CMFEditions import StandardModifiers
from Products.CMFEditions.Modifiers import ConditionalModifier
from Products.CMFEditions.Modifiers import ConditionalTalesModifier


class ModifierRegistryTool(UniqueObject, OrderedFolder):
    __doc__ = __doc__ # copy from module

    implements(
        IAttributeModifier, ISaveRetrieveModifier, ICloneModifier,
        IModifierRegistrySet,
        IModifierRegistryQuery,
#        IBulkEditableSubscriberRegistry,        # not yet implemented
        IPortalModifierTool,
    )

    id = 'portal_modifier'
    alternative_id = 'portal_modifierregistry'

    meta_type = 'Version Data Modifier Registry'

    # make interfaces, exceptions and classes available through the tool
    interfaces = KwAsAttributes(
        IConditionalModifier=IConditionalModifier,
        IConditionalTalesModifier=IConditionalTalesModifier,
    )
    exceptions = KwAsAttributes(
    )
    classes = KwAsAttributes(
        ConditionalModifier=ConditionalModifier,
        ConditionalTalesModifier=ConditionalTalesModifier,
    )
    modules = KwAsAttributes(
        StandardModifiers=StandardModifiers,
    )

    security = ClassSecurityInfo()

    def all_meta_types(self, interfaces=None):
        """Allow adding of objects implementing 'IConditionalModifier' only.
        """
        if interfaces is None:
            interfaces = (IConditionalModifier, )
        return OrderedFolder.all_meta_types(self, interfaces)

    # be aware that the tool implements also the OrderedObjectManager API

    orderedFolderSetObject = OrderedFolder._setObject
    def _setObject(self, id, object, roles=None, user=None, set_owner=1):
        """Wrap condition and modifier into one object if necessary.
        """

        # wrap the object by a conditional tales modifier if it isn't one yet
        if not IConditionalModifier.providedBy(object):
            object = ConditionalTalesModifier(id, object)

        return self.orderedFolderSetObject(id, object, roles=roles,
                                           user=user, set_owner=set_owner)

    def _collectModifiers(self, obj, interface, reversed=False):
        """ Returns a list of valid modifiers
        """
        modifier_list = []
        portal = getToolByName(self, 'portal_url').getPortalObject()
        for id, o in self.objectItems():
            # collect objects modifier only when appropriate
            if IConditionalModifier.providedBy(o) \
               and o.isApplicable(obj, portal):
                mod = o.getModifier()
                if interface.providedBy(mod):
                    modifier_list.append((id, mod))

        if reversed:
            modifier_list.reverse()

        return modifier_list

    # -------------------------------------------------------------------
    # methods implementing IModifier
    #
    #    From the viewpoint of a repository the ModifierRegistryTool is
    #    an IModifier.
    # -------------------------------------------------------------------

    security.declarePrivate('getReferencedAttributes')
    def getReferencedAttributes(self, obj):
        """See IModifier
        """
        # just loop over all objects implementing the IModifier interface.
        referenced_data = {}
        for id, mod in self._collectModifiers(obj, IAttributeModifier):
            # prepend the modifiers id to the attributes name
            template = '%s/%%s' % id
            for name, attrs in mod.getReferencedAttributes(obj).items():
                referenced_data[template % name] = attrs

        # the return value is of the format:
        #     {'<modifier_id>/<name>': <refrenced_data>, ...}
        return referenced_data

    security.declarePrivate('reattachReferencedAttributes')
    def reattachReferencedAttributes(self, obj, referenced_data):
        """
        """
        # the input of 'referenced_data' is of the format:
        #     {'<modifier_id>/<name>': <refrenced_data>, ...}
        # build a structure by modifier id
        #     {'<modifier_id>': {'<name>':< refrenced_data>, ...}, ...}
        data_by_modid = {}

        for id_name, data in referenced_data.items():
            id, name = id_name.split('/', 1)
            if not id in data_by_modid:
                data_by_modid[id] = {}
            data_by_modid[id][name] = data

        # loop over modifiers in reverse
        if data_by_modid:
            for id, mod in self._collectModifiers(obj, IAttributeModifier, reversed=True):
                if id in data_by_modid:
                    mod.reattachReferencedAttributes(obj, data_by_modid[id])

    security.declarePrivate('getOnCloneModifiers')
    def getOnCloneModifiers(self, obj):
        """See IModifier
        """
        # First check if there is at least one ICloneModifier to loop over.
        # The clone operation is much fater if there are no 'persistent_id'
        # hooks to call.
        modifiers = self._collectModifiers(obj, ICloneModifier)
        if not modifiers:
            return None

        # collect callbacks of all modifiers uplying one
        pers_id_list = []
        pers_id_nameByMeth = {}
        pers_load_byname = {}
        inside_orefs = []
        outside_orefs = []

        for id, m in modifiers:
            clone_mod = m.getOnCloneModifiers(obj)
            if clone_mod is not None:
                pers_id_list.append(clone_mod[0])
                pers_id_nameByMeth[clone_mod[0]] = id
                inside_orefs.extend(clone_mod[2])
                outside_orefs.extend(clone_mod[3])
                pers_load_byname[id] = clone_mod[1]

        def persistent_id(obj):
            # loop over modifiers having a persistent_id callback
            for pers_id in pers_id_list:
                pid = pers_id(obj)
                if pid is not None:
                    # found a modifier, add the modifiers name to its pid
                    return "%s/%s" % (pers_id_nameByMeth[pers_id], pid)

        def persistent_load(named_pid):
            # call the right modifiers persistent_load callback
            name, pid = named_pid.split('/', 1)
            return pers_load_byname[name](pid)

        return persistent_id, persistent_load, inside_orefs, outside_orefs, ''

    security.declarePrivate('beforeSaveModifier')
    def beforeSaveModifier(self, obj, obj_clone):
        """See IModifier
        """
        inside_crefs = []
        outside_crefs = []
        metadata = {}

        # just loop over all modifiers
        for ignored_id, mod in self._collectModifiers(obj, ISaveRetrieveModifier):
            mdata, icrefs, ocrefs = mod.beforeSaveModifier(obj, obj_clone)
            inside_crefs.extend(icrefs)
            outside_crefs.extend(ocrefs)
            metadata.update(mdata)

        return metadata, inside_crefs, outside_crefs

    security.declarePrivate('afterRetrieveModifier')
    def afterRetrieveModifier(self, obj, repo_clone, preserve=None):
        """See IModifier
        """
        if preserve is None:
            preserve = []
        # before letting the after retrieve modifiers replace
        # attributes save those attributes away that may got
        # overwritten but have to be preserved.
        preserved = {}
        for key in preserve:
            v = getattr(repo_clone, key, MV)
            preserved[key] = v

        orig_preserved = preserved.copy()
        # just loop over all modifiers in reverse order
        refs_to_be_deleted = []
        attrs_handling_subobjects = []
        for ignored_id, mod in self._collectModifiers(obj, ISaveRetrieveModifier, reversed=True):
            to_be_del, attrs, preserve = mod.afterRetrieveModifier(obj, repo_clone)
            refs_to_be_deleted.extend(to_be_del)
            attrs_handling_subobjects.extend(attrs)
            preserved.update(preserve)

        # Make sure that the original preserved values override
        preserved.update(orig_preserved)

        return refs_to_be_deleted, attrs_handling_subobjects, preserved

    # -------------------------------------------------------------------
    # methods implementing IModifierRegistrySet and IModifierRegistryQuery
    #
    #    The ModifierRegistryTool is also a registry of IModifier objects.
    # -------------------------------------------------------------------

    security.declareProtected(ManagePortal, 'register')
    def register(self, id, modifier, pos=-1):
        """See IModifierRegistrySet
        """
        # add the modifier
        id = self._setObject(id, modifier)

        # move it to the specified position, unfortunately the
        # the ordered object manager isn't able to count the position from
        # the end using negative numbers.
        if pos < 0:
            pos += max(0, len(self.objectIds()) + 1)
        self.moveObjectToPosition(id, pos)

    security.declareProtected(ManagePortal, 'unregister')
    def unregister(self, id):
        """See IModifierRegistrySet
        """
        self.manage_delObjects(ids=[id])

    security.declareProtected(ManagePortal, 'edit')
    def edit(self, id, enabled=None, condition=None):
        """See IModifierRegistrySet
        """
        modifier = self.get(id)
        if IConditionalTalesModifier.providedBy(modifier):
            modifier.edit(enabled, condition)
        else:
            if condition:
                raise NotImplementedError(
                    '%s does not implement conditions.' % modifier)
            modifier.edit(enabled)

    security.declareProtected(ManagePortal, 'get')
    def get(self, id):
        """See IModifierRegistryQuery
        """
        # raises the correct exception for us
        getattr(aq_base(self), id)
        return getattr(self, id)

    security.declareProtected(ManagePortal, 'query')
    def query(self, id, default=None):
        """See IModifierRegistryQuery
        """
        try:
            return self.get(id)
        except AttributeError:
            return default


    # -------------------------------------------------------------------
    # methods implementing IBulkModifierRegistry
    # -------------------------------------------------------------------

    # not yet implemented: used for building a better UI than the Folder UI
    # It's needed as soon as possible to be able to enable/disable the
    # modifiers through the web


InitializeClass(ModifierRegistryTool)
