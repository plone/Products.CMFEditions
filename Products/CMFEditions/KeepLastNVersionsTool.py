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
"""Storage Purge Policy Tool Keeping Only the Last n Versions

$Id$
"""
__version__ = "$Revision$"

from zope.interface import implements

from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo

from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import getToolByName

from Products.CMFEditions.interfaces import IPurgePolicyTool
from Products.CMFEditions.interfaces.IPurgePolicy import IPurgePolicy

class KeepLastNVersionsTool(UniqueObject, SimpleItem, PropertyManager):
    """
    """

    implements(IPurgePolicyTool, IPurgePolicy)

    id = 'portal_purgepolicy'
    alternative_id = 'portal_keeplastnversions'

    meta_type = "CMFEditions Purge Policy Keeping Only the n last Versions"

    manage_options = PropertyManager.manage_options \
      + SimpleItem.manage_options

    maxNumberOfVersionsToKeep = -1 # disabled

    _properties = (
        {'id': 'maxNumberOfVersionsToKeep', 'type': 'int', 'mode': 'w',
         'label': "maximum number of versions to keep in the storage (set to -1 for infinite)"},
    )
    security = ClassSecurityInfo()

    # -------------------------------------------------------------------
    # methods implementing IPurgePolicy
    # -------------------------------------------------------------------

    def beforeSaveHook(self, history_id, obj, metadata={}):
        """Purge all but the n most current versions

        Purges old version so that at maximum ``maxNumberOfVersionsToKeep``
        versions reside in the history.
        """
        # check if infinite number of versions shall be stored
        if self.maxNumberOfVersionsToKeep == -1:
            # infinite: do nothing
            return True

        storage = getToolByName(self, 'portal_historiesstorage')
        currentVersion = len(storage.getHistory(history_id))
        while True:
            length = len(storage.getHistory(history_id, countPurged=False))
            if length < self.maxNumberOfVersionsToKeep:
                break
            comment = "purged on save of version %s" % currentVersion
            storage.purge(history_id, 0, metadata={'sys_metadata': {
                                                           'comment': comment}
                                                   },
                          countPurged=False)

        # save current version
        return True

    def retrieveSubstitute(self, history_id, selector, default=None):
        """Retrives the next older version

        If there isn't a next older one returns the next newer one.
        """
        if selector is None:
            selector = 0
        else:
            selector = int(selector)
        storage = getToolByName(self, 'portal_historiesstorage')
        savedSelector = selector
        while selector:
            selector -= 1
            data = storage.retrieve(history_id, selector, substitute=False)
            if data.isValid():
                return data

        selector = savedSelector
        while True:
            selector += 1
            try:
                data = storage.retrieve(history_id, selector, substitute=False)
            except storage.StorageRetrieveError:
                break

            if data.isValid():
                return data

        return default

InitializeClass(KeepLastNVersionsTool)
