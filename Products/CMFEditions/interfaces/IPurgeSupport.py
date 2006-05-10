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
"""Version Storage Purge Support 

Purging a version from the storage removes that version irrevocably.

Version purge support consists of ...

1. an enhancement of the storage API (``IPurgeSupport``) which in 
   essence adds the ability to purge a specific version from a resources 
   history ...
2. and a purge policy which at save time may automatically purge
   versions from a resources history.

The main strategy with version purge support is that the layers above
the storage layer may be left untouched. Examples:

- For manual purging a version the storage tool has to be asked. No upper 
  layers are invoked.
- For automatic purging a version a policy (implemented as tool) may 
  be installed performing the necessary purging tasks on every save 
  operation. The default implementation will be able to only keep 
  the n most current versions.
- If the archivist requests for a purged version of a resource it just 
  gets another one (e.g. the next older one, depending on the policy).
- Purged versions are just skiped when iterating over the history without 
  the for loops body code noticing anything (fortunately we already look 
  up items lazily).

$Id$
"""

from Interface import Interface, Attribute


class IPurgeSupport(Interface):
    """Storage Purge Support
    
    See the notes about the ``retrieve`` and ``getHistory`` methods 
    of ``IStorage`` and the ``__len__``, ``__getattr__`` and 
    ``__iter__`` methods of ``IHistory``.
    """
    
    def purge(history_id, selector, comment="", metadata={}):
        """Purge a Version from a Resources History
        
        Purge the given version from the given history. The metadata
        passed may be used to store informations about the reasons of
        the purging.
        """

    def retrieveUnsubstituted(history_id, selector=None):
        """Return a Version of the Resource with the Given History Id
        
        Return a ``IVersionData`` object wich may contain a purged 
        version of a resource.
        
        Reinterpretation of ``retrieve`` and ``getHistory`` is necessary:
        
        The "normal" ``retrieve`` and ``__getattr__`` (of ``IHistory``) 
        now has to return a substitute if an ``IPurgePolicy`` was found. 
        """

    def getLength(history_id, ignoretPurged=True):
        """Return the Length of the History
        
        Return the length of the resources history. Either counting
        the purged versions or not.
        
        XXX Check if we need this method to be backwards compatible with 
            ``__len__`` or if it feasable to change ``__len__``.
        
        ``__iter__`` from ``IHistory`` shall always return the next non
        purged version of the resources history.
        """


class IPurgePolicy(Interface):
    """Purge Policy
    
    Purge versions in a history according a policy.
    """

    def purge(history_id, metadata={}):
        """Purge Versions from the History According a Policy
        
        The Policy has full control over the whole history of the resource 
        and may decide to purge none, one or even more than one version.
        
        The metadata passed may be used to store informations about the 
        reasons of the purging.
        
        Hint:
        
        This method gets called before the current version get saved. 
        Signalize not to save the current version by returning ``True``.
        """
