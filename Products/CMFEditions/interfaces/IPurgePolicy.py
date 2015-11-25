# -*- coding: utf-8 -*-
#########################################################################
# Copyright (c) 2006 Gregoire Weber.
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
"""Version Storage Purge Policy

At save time control is handed over to the purge policy which has full
control over all versions from a resources history.

$Id$
"""

from zope.interface import Interface


class IPurgePolicy(Interface):
    """Purge Policy

    Purge versions in a history according a policy. The methods declared
    are called by a ``IStorage`` implementation.
    """

    def beforeSaveHook(history_id, obj, metadata={}):
        """Purge Versions from the History According a Policy

        The Policy has full control over the whole history of the resource
        and may decide to purge or alter versions in the history.

        Called before the current version is saved to the storage.
        The metadata passed is the metadata that was passed to the
        ``save`` method.

        Return True if ``obj`` has to be saved by the ``IStorage``
        implementation. Return ``False`` if the object has to be discared.
        """

    def retrieveSubstitute(history_id, selector, default=None):
        """Return a selected version of an object or a substitute

        Called by the storage if the object to be retrieved was purged.
        Implement the policy in case a client tries to retrieve a purged
        version.

        Return a substitute of ``IVersionData`` type.
        """
