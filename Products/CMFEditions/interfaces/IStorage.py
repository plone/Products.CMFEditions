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
"""Intercepts/modifies saving/retrieving of versions to/from the repository.

XXX

$Id: IStorage.py,v 1.5 2005/03/11 11:05:13 varun-rastogi Exp $
"""

from Interface import Interface, Attribute

class IStorage(Interface):
    """Manages storing and retrieving of histroy entries.
    
    
    """
    
    def isRegistered(history_id):
        """Returns True if the object is already registered.
        
        A registered object has a history.
        """
    
    def register(history_id, object, referenced_data={}, metadata={}):
        """Sets up a new history for the object and does the first save.
        
        The 'object' and the 'referenced_data' together contain the whole 
        data to be added to the history. 
        
        'object' is already a clone and needn't be cloned anymore before 
        beeing added to the history. Data in 'referenced_data' are direct 
        references to the original object and must be cloned before being 
        added to the history.
        
        'referenced_data' is a list or tuple of python references or 
        'IStreamableReference' objects.
        
        'metadata' must be a (nested) dictionary. If a 'comment' key exists
        the implementation may assume it is a human readable string.
        
        May veto the registering proces by raising a 'StorageError' 
        exception. No action is performed on repeated registering.

	Returns the value of the newest version(selector).
        """
    
    def save(history_id, object, referenced_data={}, metadata={}):
        """Appends an object current state to a history.
        
        The 'object' and the 'referenced_data' together contain the whole 
        data to be added to the history. 
        
        'object' is already a clone and needn't be cloned anymore before 
        beeing added to the history. Data in 'referenced_data' are direct 
        references to the original object and must be cloned before being 
        added to the history.
        
        'referenced_data' is a list or tuple of python references or 
        'IStreamableReference' objects.
        
        'metadata' must be a (nested) dictionary. If a 'comment' key exists
        the implementation may assume it is a human readable string.

	Returns the value of the newest version(selector).
        """

    def retrieve(history_id, selector):
        """Returns a selected version of an object, which has the given 
           history id.
        
        Returns a 'IVersionData' object.
        """

    def getHistory(history_id):
        """Returns the history of an object by the given history id.
        
        Returns a 'IHistory' object.
        """
    
    def getModificationDate(history_id, selector=None):
        """ Returns the modification date of the selected version of object
            which has the given history id.

        If selected is None, the most recent version (HEAD) is taken.
        """
         

class IHistory(Interface):
    """Iterable version history.
    """
    
    def __len__():
        """Returns the length of the history.
        """
    
    def __getattr__(version_id):
        """Returns the version of an object corresponding to the version id.
        
        The item returned is of 'IVersionData'.
        """
    
    def __iter__():
        """Returns an ordered set of versions for being looped over.
        
        The returned iterator returns 'IVersionData' objects.
        """


class IVersionData(Interface):
    """
    """
    object = Attribute(
        """The objects state at save time.
        
        To avoid temporal problems (by changing the history) this
        object has to be cloned before any change.
        """)
        
    referenced_data = Attribute(
        """Data beeing passed by reference at save time.
        
        Needs not be cloned before allowing write access. Cloning was 
        already done by the storage layer.
        """)
    
    metadata = Attribute(
        """Metadata stored alongside when the objects state was saved.
        
        Metadata has to be cloned before any write change to avoid 
        temporal problems (by changing the history).
        """)


class IStreamableReference(Interface):
    """Marks an object passed to the storage by reference as streamable.
    
    This allows the history storage to optimize saving and retrieving by
    e.g. avoiding pickling/unpickling. This is mostly interesting for
    long streams.
    """
    
    def __init__(self, obj):
        """Wrap the object to be passed to the storage.
        """
    
    def getObject(self):
        """Returns the object.
        """

class StorageError(Exception):
    """History storage exception.
    """
    pass

class StorageRetrieveError(StorageError):
    """Raised if tried to retrieve a non existent version of a resource.
    """
    pass

class StorageRegisterError(StorageError):
    """Raised if registering the resource failed.
    """
    pass
    
class StorageSaveError(StorageError):
    """Raised if saving a new version of a resource failed.
    """
    pass
    
class StorageUnregisteredError(StorageError):
    """Raised if trying to save an unregistered resource.
    """
    pass
