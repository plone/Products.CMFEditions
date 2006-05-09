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
"""Version Storage Deletion Support 

Version deletion support consists of ...

1. an enhancement of the storage API (``IDeletionSupport``) which in 
   essence adds the ability to delete a specific version from a resources 
   history ...
2. and a deletion policy which at save time may automatically delete
   versions from a resources history.

The main strategy with version deletion support is that the layers above
the storage layer may be kept untouched. Examples:

- For manual deletion of a resources version the storage tool has to be 
  asked. No upper layers are invoked.
- For automatic deletion of a resources version a policy (implemented as 
  tool) may be installed performing the necessary deletion tasks on every
  save operation. The default implementation will be able to only keep 
  the n current versions.
- If the archivist requests for a deleted version of a resource it just 
  gets another one (e.g. the next older one, depending on the policy).
- Deleted items are just skiped when iterating over the history without 
  the for loops body code noticing anything (fortunately we already look 
  up items lazily).

$Id$
"""

from Interface import Interface, Attribute


class IDeletionSupport(Interface):
    """Storage Deletion Support
    
    See the notes about the ``retrieve`` and ``getHistory`` methods 
    of ``IStorage`` and the ``__len__``, ``__getattr__`` and 
    ``__iter__`` methods of ``IHistory``.
    """
    
    def delete(history_id, version, metadata={}):
        """Delete a Version from a Resources History
        
        Delete the given version from the given history. The metadata
        passed may be used to store informations about the reasons of
        the deletion.
        """

    def retrieveUnsubstituted(history_id, selector):
        """Return a Version of the Resource with the Given History Id
        
        Return a ``IVersionData`` object wich may contain a deleted 
        version of an object.
        
        Reinterpretation of ``retrieve`` and ``getHistory`` is necessary:
        
        The "normal" ``retrieve`` and ``__getattr__`` now has to return 
        a substitute if an ``IDeletionPolicy`` was found. As well when 
        a specific version is read from the history returned from 
        ``getHistory``.
        """

    def getEffectiveLength(history_id):
        """Return the Length of the History Ignoring Deleted Versions
        
        In contrast the ``__len__`` method of the history returned still 
        has to return the length of the history *including* the deleted
        version (because upper layers may try to count from the end).
        
        XXX Check if it is necessary to be backwards compatible with 
            ``__len__``.
        
        ``__iter__`` from ``IHistory`` shall always return the next non
        deleted version of the resources history.
        """


class IDeletionPolicy(Interface):
    """Deletion Policy
    
    Delete versions in a history according a policy.
    """
    
    def delete(history_id, metadata={}):
        """Delete Versions from the History According a Policy
        
        The Policy has full control whole history of the resource and
        may decide to delete none, one or even more than one version.
        
        The metadata passed may be used to store informations about the 
        reasons of the deletion.
        
        Return ``True`` if the current version shall not be saved and 
        discarded.
        """
