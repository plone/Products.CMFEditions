#########################################################################
# Copyright (c) 2005 Gregoire Weber. 
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
"""Manages Factories for diffrenet kinds of references.

$Id: $
"""

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo, getSecurityManager

from Acquisition import aq_base
from ZODB.PersistentList import PersistentList
from OFS.OrderedFolder import OrderedFolder

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.CMFCorePermissions import ManagePortal
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from Products.CMFEditions.utilities import generateId

from Products.CMFEditions.interfaces.IReferenceFactories \
    import IReferenceFactories

class ReferenceFactoriesTool(UniqueObject, OrderedFolder, ActionProviderBase):
    __doc__ = __doc__ # copy from module

    __implements__ = (
        OrderedFolder.__implements__,   # hide underspecified interfaces :-(
        IReferenceFactories,
    )
    
    id = 'portal_referencefactories'
    alternative_id = 'portal_referencefactoryregistry'

    meta_type = 'Reference Factory Registry'
    
    security = ClassSecurityInfo()
    
    # be aware that the tool implements also the OrderedObjectManager API
    
    # -------------------------------------------------------------------
    # methods implementing IFactories
    # -------------------------------------------------------------------
    
    security.declarePrivate('invokeFactory')
    def invokeFactory(self, repo_clone, source, selector=None):
        """See IReferenceFactories
        """
        # XXX: Just assuming ObjectManager behaviour for now
        portal_hidhandler = getToolByName(self, 'portal_historyidhandler')
        portal_archivist = getToolByName(self, 'portal_archivist')
        portal_type = repo_clone.getPortalTypeName()
        id = repo_clone.getId()
        if id in source.objectIds():
            id = generateId(source, prefix=id)
        # XXX does the factory return an id or obj? If yes, use this one
        id = source.invokeFactory(portal_type, id)
        obj = getattr(source, id)
        try:
            history_id = portal_hidhandler.getUid(repo_clone)
            portal_hidhandler.setUid(obj, history_id)
        except portal_hidhandler.UniqueIdError:
            portal_hidhandler.register(obj)
        
        # XXX check catalog integrity on retrieve!!!
        
        return obj

    security.declarePrivate('hasBeenMoved')
    def hasBeenMoved(self, obj, source):
        """See IReferenceFactories
        """
        # XXX: Just assuming ObjectManager behaviour for now
        return getattr(aq_base(source), obj.getId(), None) is None

InitializeClass(ReferenceFactoriesTool)
