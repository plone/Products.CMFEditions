#########################################################################
# Copyright (c) 2005 Alberto Berti, Gregoire Weber.
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
"""Modifier wrappers

"""

from AccessControl.class_init import InitializeClass
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.Expression import Expression
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IModifier import IConditionalModifier
from Products.CMFEditions.interfaces.IModifier import IConditionalTalesModifier
from Products.PageTemplates.Expressions import getEngine
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from ZODB.broken import Broken
from zope.interface import implementer


manage_addModifierForm = PageTemplateFile(
    "www/modifierAddForm.pt", globals(), __name__="manage_addModifierForm"
)


@implementer(
    IConditionalModifier,
)
class ConditionalModifier(SimpleItem):
    """This is a wrapper for a modifier."""

    modifierEditForm = PageTemplateFile(
        "www/modifierEditForm.pt", globals(), __name__="modifierEditForm"
    )
    modifierEditForm._owner = None
    manage = manage_main = modifierEditForm
    manage_options = (
        {"label": "Edit", "action": "modifierEditForm"},
    ) + SimpleItem.manage_options[:]

    def __init__(self, id, modifier, title=""):
        """See IConditionalModifier."""
        self.id = str(id)
        self.title = str(title)
        self.meta_type = "edmod_%s" % id
        self._modifier = modifier
        self._enabled = False

    def edit(self, enabled=None, title="", REQUEST=None):
        """See IConditionalModifier."""
        self.title = title

        if enabled is not None and (
            enabled == "True" or (isinstance(enabled, bool) and enabled)
        ):
            self._enabled = enabled
        else:
            self._enabled = False

        if REQUEST:
            REQUEST.set("manage_tabs_message", "Changed")
            return self.modifierEditForm(self, REQUEST)

    def isBroken(self):
        """Is the modifier broken?

        This happens if the underlying class no longer exists.
        """
        return isinstance(self.getModifier(), Broken)

    def isApplicable(self, obj, portal=None):
        """See IConditionalModifier."""
        # check if disabled or an empty condition and not broken
        if self._enabled and not self.isBroken():
            return True

    def isEnabled(self):
        """See IConditionalModifier."""
        return self._enabled

    def getModifier(self):
        """See IConditionalModifier."""
        return self._modifier


InitializeClass(ConditionalModifier)


manage_addTalesModifierForm = PageTemplateFile(
    "www/talesModifierAddForm.pt", globals(), __name__="manage_addTalesModifierForm"
)


@implementer(
    IConditionalTalesModifier,
)
class ConditionalTalesModifier(ConditionalModifier):
    """This is a wrapper with a tales condition for a modifier."""

    modifierEditForm = PageTemplateFile(
        "www/talesModifierEditForm.pt", globals(), __name__="modifierEditForm"
    )
    manage_options = (
        {"label": "Edit", "action": "modifierEditForm"},
    ) + ConditionalModifier.manage_options[:]

    def __init__(self, id, modifier, title=""):
        """See IConditionalTalesModifier."""
        ConditionalModifier.__init__(self, id, modifier, title)
        self._condition = None

    def edit(self, enabled=None, condition=None, title="", REQUEST=None):
        """See IConditionalTalesModifier."""
        ConditionalModifier.edit(self, enabled, title)
        if condition is not None and condition != self.getTalesCondition():
            self._condition = Expression(condition)

        if REQUEST:
            REQUEST.set("manage_tabs_message", "Changed")
            return self.modifierEditForm(self, REQUEST)

    def isApplicable(self, obj, portal=None):
        """See IConditionalTalesModifier."""
        # check if disabled or an empty condition or broken
        if not self._enabled or not self.getTalesCondition() or self.isBroken():
            return False

        # create the expression context and return result
        context = createExpressionContext(obj, portal)
        return self._condition(context)

    def getTalesCondition(self):
        """See IConditionalTalesModifier."""
        return getattr(self._condition, "text", "")


InitializeClass(ConditionalTalesModifier)


def createExpressionContext(obj, portal=None, **more_symbols):
    """Creates a valid context for the expression.

    Tal expressions need a context in order to do the evaluation.
    obj is the object that will be mapped to "object" in the
    expression's context.
    Other symbols like "repo_clone" and "obj_clone" can be passed as keyword
    arguments.
    """

    def findNextFolderishParent(obj):
        """Try to find the folder of the given object by aquisition.

        XXX what's the correct strategy in Zope2 land to check for a folder?
            what's most relyable?
            a) check if isPrincipiaFolderish is True?
            b) check if the object is an ObjectManager?
            c) other?

            We have to do the right thing here to get things working
            correctly. I hope all the products out there do the right
            thing also ...
        """
        # XXX propose this check (should be the same):
        #    if aq_base(obj) is obj:
        if obj is None or not hasattr(obj, "aq_base"):
            folder = None
        else:
            folder = obj
            # Search up the containment hierarchy until we find an
            # obj that claims it's a folder.
            while folder is not None:
                if getattr(aq_base(folder), "isPrincipiaFolderish", 0):
                    # found it.
                    break
                else:
                    folder = aq_parent(aq_inner(folder))
        return folder

    try:
        obj_url = obj.absolute_url()
    except AttributeError:
        obj_url = ""

    # use the portal if folder lookup fails due to an unwrapped obj
    folder = findNextFolderishParent(obj) or portal

    pm = getToolByName(portal, "portal_membership", None)
    if pm is None or pm.isAnonymousUser():
        member = None
    else:
        member = pm.getAuthenticatedMember()

    try:
        meta_type = obj.meta_type
    except AttributeError:
        meta_type = None

    try:
        portal_type = obj.getPortalTypeName()
    except AttributeError:
        portal_type = None

    data = {
        "object_url": obj_url,
        "folder_url": folder is not None and folder.absolute_url() or "",
        "portal_url": portal is not None and portal.absolute_url() or "",
        "object": obj,
        "folder": folder,
        "portal": portal,
        "nothing": None,
        "request": getattr(obj, "REQUEST", None),
        "modules": SecureModuleImporter,
        "member": member,
        "meta_type": meta_type,
        "portal_type": portal_type,
    }
    data.update(more_symbols)
    return getEngine().getContext(data)
