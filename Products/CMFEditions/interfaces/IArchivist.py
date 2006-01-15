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


$Id: IArchivist.py,v 1.3 2005/02/23 00:29:02 gregweb Exp $
"""

from Interface import Interface, Attribute


class IArchivist(Interface):
    """The archivist knows how to handle saving and retrieving versionable 
       aspects.
    
    It decides which aspects to save to a histories storage and which
    aspects have to be overridden by the working copies ones on retrieve.
    
    As object ``obj`` may be passed a python reference to the object or
    any other kind of reference that allows the archivist dereferencing
    the object meant.
    """

    def prepare(obj, app_metadata=None, sys_metadata={}):
        """Prepares saving and registering of versionable aspects.
        
        The archivist decides which aspects of the objects are prepared
        to be saved and which not.
        
        Doesn't do any save operation, just returns information
        to allow recursively save the object.
        
        Returns an 'IPreparedObject' object.
        """

    def register(prepared_obj):
        """Register the object saving the initial state.
        
        Prior to a register the object has to prepared. Pass the
        return value of the 'prepare' method to 'prepared_obj'.
        """

    def save(prepared_obj, autoregister=None):
        """Saves versionable aspects of the objects current state.
        
        Set 'autoregister' to True if the object shall be registered
        automatically at the first save ever.
        
        Prior to a save the object has to be prepared. Pass the
        return value of the 'prepare' method to 'prepared_obj'.
        """

    def isUpToDate(obj=None, history_id=None, selector=None):
        """Returns True if the working copy has changed since the last save
           or revert compared to the selected version. If selector is None,
           the comparison is done with the HEAD.
                                                                                                                             
        The working copy is up to date if the modification date is the
        identical to the selected version.
        """

    def retrieve(obj=None, history_id=None, selector=None, preserve=()):
        """Retrieves a former state of an object.
        
        Requires either an object which is the working copy, or a history_id
        for an object if no history_id is provided the history_id will be 
        obtained from the working copy object.
        
        Returns an 'IVersionData' object.
        
        Set the selector to None if you like to retrieve the most actual
        version.
        
        Modifiers may overwrite some aspects of the retrieved version by
        the equivalent aspects of the working copy. Sometimes the 
        overwritten information is from interest. Attributes (and 
        subattributes) beeing from interest can be passed with the
        'preserve' argument. 
        E.g. preserve=('family_name', 'nick_name', 'real_name')
        """

    def getHistory(obj=None, history_id=None, preserve=()):
        """Returns the history of an object.
        
        The history is a 'IHistory' object.
        
        Requires either an object which is the working copy, or a history_id
        for an object if no history_id is provided the history_id will be 
        obtained from the working copy object.
        
        Raises an 'ArchivistError' exception if the given object doesn't
        have a history.
        
        Modifiers may overwrite some aspects of the retrieved version by
        the equivalent aspects of the working copy. Sometimes the 
        overwritten information is from interest. Attributes (and 
        subattributes) beeing from interest can be passed with the
        'preserve' argument. 
        E.g. preserve=('family_name', 'nick_name', 'real_name')
        """

    def queryHistory(obj=None, history_id=None, preserve=(), default=[]):
        """Returns the history of an object.
        
        Requires either an object which is the working copy, or a history_id
        for an object if no history_id is provided the history_id will be 
        obtained from the working copy object.
        
        The history is a 'IHistory' object.
        
        Returns the default value if the given object doesn't have a 
        history.
        
        Modifiers may overwrite some aspects of the retrieved version by
        the equivalent aspects of the working copy. Sometimes the 
        overwritten information is from interest. Attributes (and 
        subattributes) beeing from interest can be passed with the
        'preserve' argument. 
        E.g. preserve=('family_name', 'nick_name', 'real_name')
        """


class IPreparedObject(Interface):
    """Contains data prepared for save or register.
    """

    history_id = Attribute(
        """The id of the objects history.
        """)

    original = Attribute(
        """The unaltered original object before the modifiers were applied.
        
        This is a 'IObjectData' object.
        
        The original object shall not be modified!
        """)
    
    clone = Attribute(
        """The cloned object and version aware reference info.
        
        This is a 'IObjectData' object.
        """)
    
    referenced_data = Attribute(
        """Data that is passed to the storage by reference.
        
        These is an optimization for the case where a big blob (e.g. a Word 
        file) has to be saved but you want to avoid costy cloning beeing done 
        by the archivist.
        
        Returns a dictionary of the following format:
        
            {'name': pyref_to_object, ...}
        """)
    
    metadata = Attribute(
        """Metadata to be passed to history storage.
        """)
        
    is_registered = Attribute(
        """True if already registered by the Archivist.
        """)


class IVersionData(Interface):
    """
    """
    
    data = Attribute(
        """The previously saved object.
        
        This is a 'IObjectData' object.
        """)
    
    refs_to_be_deleted = Attribute(
        """List of references to be deleted on revert.
        
        The items (containing the reference informations) are of 
        ``IReferenceAdapter``.
        """)
    
    attr_handling_references = Attribute(
        """List of names of attributes handling references.
        """)
        
    preserved_data = Attribute(
        """Returns data beeing preserved from beeing overwritten by modifiers.
        
        The preserved data is a flat dictionary. With the example from above:
        nick_name = obj.preserved_data['nick_name']
        """)
    
    sys_metadata = Attribute(
        """System related metadata.
        
        A Dictionary with the following keys:
        
        - timestamp: save time
        - principal: the actor that did the save
        - XXX path: the path at store time (in getPhysicalPath format)
        """)
        
    app_metadata = Attribute(
        """Metadata stored alongside when the objects state was saved.
        """)


class IHistory(Interface):
    """Iterable version history.
    """

    def __init__(archivist, obj):
        """Instantiates a lazy iterable history.
        
        This is a multi adapter adpating the archivist, the object and
        optionally a context wrapper.
        """

    def __len__():
        """Returns the length of the history.
        """

    def __getattr__(version_id): # XXX or get or both?
        """Returns the version of an object corresponding to the version id.
        
        The object returned is of 'IVersionData'.
        """

    def __iter__():
        """Returns an ordered set of versions for beeing looped over.
        
        The objects returned are of 'IVersionData'.
        """


class IObjectData(Interface):
    """The object including informations about outgoing references.
    """
    
    object = Attribute(
        """The object with some of the python references replaced by 
           version aware references.
        """)
        
    inside_refs = Attribute(
        """List of 'IAttributeAdapter' objects adapting "object inside"
           'IVersionAwareReference'.
        """)

    outside_refs = Attribute(
        """List of 'IAttributeAdapter' objects adapting "object outside"
           'IVersionAwareReference'.
        """)


class IAttributeAdapter(Interface):
    """Adapter allowing setting and getting an attribute.
    
    TODO: use ``Attribute`` instead of explicit setters/getters.
    TODO: remove ``__init__`` from signature.
    """
    
    def __init__(parent, attr_name, type=None):
        """Store the attributes "coordinates".
        """
        
    def setAttribute(obj):
        """Sets the given object as attribute.
        """
        
    def getAttribute():
        """Returns the current attribute.
        """
        
    def getAttributeName():
        """Returns the attributes name.
        """
    
    def getType():
        """Returns the attributes type.
        """


class IVersionAwareReference(Interface):
    """A version aware reference references an object in the repository.
    
    It is used to replace python references on save time and may be used 
    to rebuild those at retrieve time.
    """

    def __init__(**info):
        """Store some info with the reference.
        
        referencing scenarios:
        
         hid  | vid  | lid  | remarks
        ------+------+------+---------------------------------------------
         None | d.c. | d.c. | no reference stored (reference lost on save)
         True | None | None | reference to a non versionable resource or
              |      |      | or version and location information was not
              |      |      | known or was irrelevant at save time
         True | None | True | reference to a specific location of a 
              |      |      | resource (one of more working copies)
         True | True | None | impossible combination
         True | True | True | reference to s specific version of a 
              |      |      | resource at a specific location
        
        abrev.: hid = history_id, vid = version_id, lid = location_id
                "True" means "True value" in the above table.
        
        Caution: The 'info' passed gets pickled. So take care not to 
                 store deeply nested objects!!!
        """

    def setReference(target_obj, remove_info=True):
        """Set a reference to the given target object.
        """
    
    history_id = Attribute(
        """The history id of the referenced resource.
        
        Histories usually contain more than one version of a resource.
        
        May be None. In this case the reference isn't set yet or the
        target object isn't referenceable.
        """)
        
    version_id = Attribute(
        """The version id of the referenced resource.
        
        May be None. For the interpretation see above.
        """)
        
    location_id = Attribute(
        """The location id of the working copy of the referenced resource.
        
        May be None. For the interpretation see above.
        """)
        
    info = Attribute(
        """The info stored alongside on instantiation time.
        
        May not exist.
        """)


class ArchivistError(Exception):
    """Archivist exception
    """
    pass

class ArchivistRetrieveError(ArchivistError):
    """Raised if tried to retrieve a non existent version of a resource.
    """
    pass

class ArchivistRegisterError(ArchivistError):
    """Raised if registering the resource failed.
    """
    pass
    
class ArchivistSaveError(ArchivistError):
    """Raised if saving a new version of a resource failed.
    """
    pass
    
class ArchivistUnregisteredError(ArchivistError):
    """Raised if trying to save an unregistered resource.
    """
    pass
