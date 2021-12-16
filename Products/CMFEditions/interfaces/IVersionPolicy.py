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
"""Version Policies
"""
from zope.interface import Interface


class IVersionPolicy(Interface):
    """A version policy object, which describes and sets up a versioning
    policy
    """

    def Title():
        """Returns a nice name for the policy"""

    # Some optional hooks used to set up the policy if available
    # these will be called when the corresponding action is taken in
    # portal_repository.  Make sure these take keyword arguments as some
    # may be passed on manage_changePolicyDefs or manage_setTypePolicies.

    # def setupPolicyHook(portal, **kw)
    #     """Performs setup actions when a policy is added to a portal"""

    # def removePolicyHook(portal, **kw)
    #     """Performs teardown actions when a policy is added to a portal"""

    # def enablePolicyOnTypeHook(portal, type, **kw)
    #     """Performs setup actions when a policy is enabled on a type"""

    # def disablePolicyOnTypeHook(portal, type, **kw)
    #     """Performs teardown actions when a policy is enabled on a type"""
