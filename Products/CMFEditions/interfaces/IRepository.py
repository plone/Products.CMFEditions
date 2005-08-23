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

Terminology
-----------

content
  May be any kind of content, like a document, an image etc.
  The term doesn't carry any information about which version is talked about.
  Many different versions of a content may exist.

version
  The state of a content at a given time.

working copy
  A specific version of a content living in the Zope tree.

former version
  A specific version in the past.


$Id: IRepository.py,v 1.8 2005/04/01 17:41:56 disommav Exp $
"""

from Interface import Interface, Attribute


class IVersionSupport(Interface):
    """Check if versioning is supported for a specific content.
    """

    def isVersionable(obj):
        """Returns True if the object is versionable
        """


class IContentTypeVersionSupport(IVersionSupport):
    """Registry for versionable content types
    """

    def getVersionableContentTypes():
        """Returns a list of Versionable content types
        """

    def setVersionableContentTypes(new_content_types):
        """Set the list of Versionable content types
        """

class IContentTypeVersionPolicySupport(IContentTypeVersionSupport):
    """Determine if a type supports a particular versioning method, the policy
       parameter is simply a string representing the policy"""

    def addPolicyForContentType(content_type, policy):
        """Sets a content type to use a specific policy"""

    def removePolicyFromContentType(content_type, policy):
        """Sets a content type to use a specific policy"""

    def supportsPolicy(obj, policy):
        """Determine if an object is set to use a specific versioning policy
        """

    def hasPolicy(obj):
        """Determine if an object has any assigned versioning policies"""

    def manage_setTypePolicies(policy_map):
        """Set the policy_mapping for all types from a dict of
        content_type : policy list mappings {content_type: [policy1, policy2]}
        """

    def listPolicies():
        """Return a sequence of all defined VersionPolicy objects"""

    def addPolicy(policy_id, policy_title):
        """Add a new versioning policy and friendly name for that policy,
           will update the title of an existing policy."""

    def removePolicy(policy_id):
        """Removes a versioning policy from the tool and all types which
           support it"""

    def manage_changePolicyDefs(policy_list):
        """Update the policy structure with a list of tuples [(id, title),...]
        """

    def getPolicyMap():
        """Return a mapping of types to the lists of policies they support,
           for use in config screen."""

class ICopyModifyMergeRepository(Interface):
    """The simplest repository possible.

    This component exposes the main API.
    """

    def isVersionable(obj):
        """Return True if the content type is versionable.
        """

    def setAutoApplyMode(autoapply):
        """Sets the autoapply mode.

        Before a repository can host a version of a content it has to be
        registred.
        If True the first 'save' operation will register the content
        automatically and applies version control.
        The default value is True.
        """

    def applyVersionControl(obj, comment='', metadata={}):
        """Register the content to the repository.

        Must be called prior any of the other repository related methods.
        Not necessary if 'autoapply' is set to a True.
        'comment' preferably is a human readable string comment.
        'metadata' must be a dictionary.
        This operation save the current version of the working copy as
        first version to the repository.
        """

    def save(obj, comment='', metadata={}):
        """Saves the current version of the content.

        'comment' preferably is a human readable string comment.
        'metadata' must be a dictionary.
        """

    def revert(obj, selector=None):
        """Reverts to a former version of the content by replacing the working
        copy.

        Reverts to the most recently saved version if no selector
        is passed.
        """

    def retrieve(obj, selector=None, preserve=()):
        """Returns a former version of a content without replacing the working
        copy.

        It returns an ``IVersionData`` object and doesn't modify the working
        copy in any way.
        """

    def isUpToDate(obj):
        """Returns True if the working copy is modified.
        """

    def getHistory(obj, preserve=()):
        """Returns the history of a content.

        Returns a sequence (``IHistory``) of ``IVersionData`` objects.
        """


class IVersionData(Interface):
    """ Used to store the versioned content plus additional data.
    """

    object = Attribute(
        """The retrieved version of the content.
        """)

    preserved_data = Attribute(
        """It is the data preserved from overwriting during the
        retrive process.

        The preserved data is a flat dictionary.
        With the example from above:
                nick_name = vdata.preserved_data['nick_name']
        """)

    comment = Attribute(
        """The comment stored when the working copies version was saved.
        """)

    metadata = Attribute(
        """Metadata stored when the working copies version was saved.
        """)

    sys_metadata = Attribute(
        """System related metadata.

        A Dictionary with the following keys:
        - timestamp: save time
        - principal: the actor that did the save
        """)


class IHistory(Interface):
    """Iterable version history.
    """

    def __len__():
        """Returns the length of the history.
        """

    def __getattr__(selector):
        """Returns the selected version of a content.

        Returns a ``IVersionData`` object.
        """

    def __iter__():
        """ Returns an iterator returning 'IVersionData' object.
        """

class IVersionPolicy(Interface):
    """A version policy object, currently just a title and an Id"""
    def Title():
        """Returns a nice name for the policy"""