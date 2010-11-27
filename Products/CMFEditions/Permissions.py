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
"""Permissions

$Id: Permissions.py,v 1.1 2005/02/13 11:52:58 gregweb Exp $
"""

from Products.CMFCore.permissions import setDefaultRoles

ApplyVersionControl = 'CMFEditions: Apply version control'
setDefaultRoles(ApplyVersionControl, ('Manager', 'Site Administrator'))

SaveNewVersion = 'CMFEditions: Save new version'
setDefaultRoles(SaveNewVersion, ('Manager', 'Site Administrator'))

PurgeVersion = 'CMFEditions: Purge version'
setDefaultRoles(PurgeVersion, ('Manager', 'Site Administrator'))

AccessPreviousVersions = 'CMFEditions: Access previous versions'
setDefaultRoles(AccessPreviousVersions, ('Manager', 'Site Administrator'))

RevertToPreviousVersions = 'CMFEditions: Revert to previous versions'
setDefaultRoles(RevertToPreviousVersions, ('Manager', 'Site Administrator'))

CheckoutToLocation = 'CMFEditions: Checkout to location'
setDefaultRoles(CheckoutToLocation, ('Manager', 'Site Administrator'))

ManageVersioningPolicies = 'CMFEditions: Manage versioning policies'
setDefaultRoles(ManageVersioningPolicies, ('Manager', 'Site Administrator'))

