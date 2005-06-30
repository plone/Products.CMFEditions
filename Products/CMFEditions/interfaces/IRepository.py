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
"""Repository strategies

The functionality and naming of the repository strategies is based on:

  http://tortoisesvn.tigris.org/docs/TortoiseSVN_en/ch02s02.html


Terminology
-----------

resource
  Generic term. May be any kind of content, like a document, an image etc. 
  The term doesn't carry any information about which version is talked about. 
  Frome a resource many different versions may exist.

version
  The state of a resource at a given time.

working copy
  A specific version of a resource living in the Zope tree.

former state
  A specific version in the past.


$Id: IRepository.py,v 1.8 2005/04/01 17:41:56 disommav Exp $
"""

from Interface import Interface, Attribute

class ICopyModifyMergeRepository(Interface):
    """The simples possible repository allowing parallel editing.
    
    In this model, many working copies at different places may exist. 
    Users may work in parallel, modifying copies in different places. 
    Finally, the copies are merged together into a new, final version. 
    
    Merging has to be done on application level, the repository does 
    not support merging.
    """
    
    def isVersionable(obj):
        """Return true if the content type is versiable, false otherwise

        This method is used to check whether a certain content type can be
        versioned or not"""

    def setAutoApplyMode(autoapply):
        """Sets the autoapply mde.
        
        If True the first 'save' operation also applies version control.
        The default value is False.
        """
    
    def applyVersionControl(obj, comment='', metadata={}):
        """Puts the working copy under version control.
        
        Must be called prior any of the other repository related methods 
        are used. Not necessary if 'autoapply' is set to a true value.
        
        'comment' preferably is a human readable string comment. 'metadata' 
        must be a dictionary. It may be a nested dictionary.
        
        This operation save the current state of the working copy as 
        first version to the repository.
        """
    
    def save(obj, comment='', metadata={}):
        """Saves the current state of the working copy for later retrieval.
        
        'comment' preferably is a human readable string comment. 'metadata' 
        must be a dictionary. It may be a nested dictionary.
        """
    
    def revert(obj, selector=None):
        """Reverts to a former state of the resource.
        
        Replaces the current working copy by the former state of the 
        resource. Reverts to the most recently saved state if no selector 
        is passed.
        """
    
    def retrieve(obj, selector=None, preserve=()):
        """Returns a former state of a resource.
        
        This does nearly the same as 'revert' except that it doesn't 
        replace the working copy. Instead it returns a 'IVersionData' 
        object containing the former state of the resource plus 
        additional informations.
        
        As modifiers may overwrite some aspects of the former state by 
        the current working copies aspects one may loose important 
        information. By passing attribute names in the 'preserve' 
        parameter accessing those aspects is possible (see 
        'preserved_data' in 'IVersionData')
        """
    
    def isUpToDate(obj, selector=None):
        """Returns True if the working copy is modified since the last save
           or revert compared to the selected version. If selector is None,
           the comparison is done with the HEAD.
        
        The working copy is up to date if the modification date is the 
        identical to the selected version.
        """
        
    def getHistory(obj, preserve=()):
        """Returns the history of a resource.
        
        Returns a (list like) 'IHistory' object. Actually the entries 
        in the returned list like object are the same as the ones returned 
        by 'retrieve'.
        
        For a description of 'preserve' see 'retrieve'. 
        
        "Intelligent" implementations return the entries lazyly.
        
        Only returns the versions of resource living in the repository.
        Does not return working copies.
        """
        
    def checkout(history_id, container, version_id=None, preserve=()):
        """Checks out a former state of a resource to the given container.
        
        In fact checking out a former state of a resource is like 
        instantiating a fresh resource of the same portal type in the
        given container, giving it the identity of the resource with the 
        given history id and then finaly doing a 'revert' to the given 
        version id.
        
        For a description of 'preserve' see 'retrieve'. 
        
        This method allows checking out a resource to multiple locations.
        """
        
        
    def getHistoryById(history_id):
        """Returns the history of a resource by history id.
        
        Returns a (list like) 'IHistory' object.
        
        The difference to the 'getHistory' method is that there is no
        working copy available overriding aspects of the retrieved state.
        
        Only returns the versions of resource living in the repository.
        Does not return working copies.
        """

class IVersionData(Interface):
    """
    """
    
    object = Attribute(
        """The retrieved version of the working copy.
        """)
    
    preserved_data = Attribute(
        """Returns data beeing preserved from beeing overwritten by modifiers.
        
        The preserved data is a flat dictionary. With the example from above:
        nick_name = vdata.preserved_data['nick_name']
        """)
    
    comment = Attribute(
        """The comment stored when the working copies state was saved.
        """)
    
    metadata = Attribute(
        """Metadata stored when the working copies state was saved.
        """)

    sys_metadata = Attribute(
        """System related metadata.
        
        A Dictionary with the following keys:
        
        - timestamp: save time
        - principal: the actor that did the save
        - XXX path: the path at store time (in getPhysicalPath format)
        """)


class IHistory(Interface):
    """Iterable version history.
    """

    def __len__():
        """Returns the length of the history.
        """

    def __getattr__(selector):
        """Returns the version of a working copy.
        
        Returns a 'IVersionData' object.
        """

    def __iter__():
        """Returns an ordered set of versions for beeing looped over.
        
        Returns an iterator returning 'IVersionData' object.
        """


# XXX The following interface is work in progresss.
# XXX It's here only for the sake of completeness.

class ILockModifyUnlockRepository(ICopyModifyMergeRepository):
    """Repository allowing only one working copy be edited at the same time.
    
    Use this in a multi location checkout szenario to ensure that saves to 
    the repository may be done from only one location. Doesn't lock any 
    working copy.
    """

    def lock(obj):
        """Locks the working copy for exclusive save rights.
        
        Raises an exception if the working copy can not be allocated.
        
        XXX alternative names:
        
        - allocate
        - book
        """
    
    def unlock(obj):
        """Unlocks the working copy from exclusive save rights.
        
        XXX alternative names:
        
        - release
        - free
        """
    
    def isLocked(obj):
        """Returns True if the given working copy is locked.
        
        XXX alternative names:
        
        - isAllocated
        - isBooked
        """

    def forceUnlock(obj):
        """Breaks an existing lock.
        """
