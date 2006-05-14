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
    
    Add ``purge`` and extend the signature of ``retrieve`` and 
    ``getHistory``. The defaults of the extended methods mimique the
    behaviour of ``IStorage``.
    """
    
    def retrieve(history_id, selector, countPurged=True, substitute=True):
        """Return the Version of the Resource with the given History Id
        
        Overrides ``retrieve`` from ``IStorage`` by adding ``countPurged`` 
        and ``substitute`` parameters.
        
        If ``countPurged`` is ``True`` purged versions are taken into
        account also. If ``False`` purged versions are ignored and not
        taken into account in counting.
        
        If ``substitute`` is ``True`` a substitute is returned in case
        the requested version was purged before.
        
        Return a ``IVersionData`` object.
        """

    def getHistory(history_id, countPurged=True, substitute=True):
        """Returns the history of an object by the given history id.
        
        Overrides ``getHistory`` from ``IStorage`` by adding 
        ``countPurged`` and ``substitute`` parameters.
        
        If ``countPurged`` is ``True`` purged versions are returned also. 
        If ``False`` purged versions aren't returned.
        
        If ``substitute`` is ``True`` a substitute is returned in case
        the requested version was purged before.
        
        Return a ``IHistory`` object.
        """

    def purge(history_id, selector, comment="", metadata={}, 
              countPurged=True):
        """Purge a Version from a Resources History
        
        If ``countPurged`` is ``True`` version numbering counts purged
        versions also. If ``False`` purged versiona are not taken into 
        account.
        
        Purge the given version from the given history. The metadata
        passed may be used to store informations about the reasons of
        the purging.
        """


class IPurgePolicy(Interface):
    """Purge Policy
    
    Purge versions in a history according a policy.
    """

    def beforeSaveHook(history_id, metadata={}):
        """Purge Versions from the History According a Policy
        
        The Policy has full control over the whole history of the resource 
        and may decide to purge or alter versions in the history.
        
        The metadata passed is the metadata that was passed to the 
        ``save`` method.
        
        Hint:
        
        This method gets called before the current version get saved. 
        Signalize not to save the current version by returning ``False``.
        """

    def retrieveSubstitute(history_id, selector, default=None):
        """Return a selected version of an object or a substitute
        
        Called by the storage if the object to be retrieved was purged.
        Implement the policy in case a client tries to retrieve a purged
        version.
        
        Return a 'IVersionData' object.
        """
