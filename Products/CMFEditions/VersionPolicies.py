#########################################################################
# Copyright (c) 2004, 2005 Alec Mitchell
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
"""Default Version Policy implementations.

"""

from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from Products.CMFEditions.interfaces.IVersionPolicy import IVersionPolicy
from zope.interface import implementer


@implementer(IVersionPolicy)
class VersionPolicy(SimpleItem):
    """A simple class for storing version policy information"""

    security = ClassSecurityInfo()

    def __init__(self, obj_id, title, **kw):
        self.id = obj_id
        self.title = title

    security.declarePublic("Title")

    def Title(self):
        return self.title


class ATVersionOnEditPolicy(VersionPolicy):
    """A policy that implements version creation on edit.

    The 'AT' is the name points to Archetypes, but it works for Dexterity as well.
    For Archetypes we used to need portal_form_controller overrides,
    which we installed in a setupPolicyHook method and removed in removePolicyHook.
    In Plone 5.2 this is no longer needed, and in Plone 6 we no longer support Archetypes.

    But the policy class still needs to exist, because this is stored persistently.
    And an instance of it with id 'at_edit_autoversion' needs to be registered,
    as is done in our profiles/default/repositorytool.xml.

    The controlpanel (with code in CMFPlone) expects this id.
    So does plone.app.versioningbehavior.
    Most importantly: if a policy with this id is enabled for a portal_type,
    no matter which class is behind it, a new version is stored on edit.
    """

    pass
