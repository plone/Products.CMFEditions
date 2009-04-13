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
"""Unique Id Handler Tool

Provides support for accessing unique ids on content object.

$Id: UniqueIdHandlerTool.py,v 1.2 2005/01/06 14:25:44 gregweb Exp $
"""

from zope.interface import implements

from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo

from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import getToolByName, UniqueObject
from Products.CMFCore.permissions import ManagePortal

from Products.CMFUid.interfaces import IUniqueIdHandler
from Products.CMFUid.interfaces import IUniqueIdBrainQuery
from Products.CMFUid.interfaces import UniqueIdError

UID_ATTRIBUTE_NAME = 'cmf_uid'

class UniqueIdHandlerTool(UniqueObject, SimpleItem):
    __doc__ = __doc__ # copy from module

    implements(IUniqueIdHandler, IUniqueIdBrainQuery)

    id = 'portal_historyidhandler'
    alternative_id = "portal_editions_uidhandler"
    meta_type = 'Unique Id Handler Tool'
    
    # make the uid attribute name available for the unit tests
    # not meant to be altered as long you don't know what you do!!!
    UID_ATTRIBUTE_NAME = UID_ATTRIBUTE_NAME
    
    # make the exception class available through the tool
    UniqueIdError = UniqueIdError
    
    security = ClassSecurityInfo()
    
    # ----------------------------------------------------------------
    # The following methods have to be made location_id aware to allow
    # applications beeing version_id aware also.
    # ----------------------------------------------------------------
    
    security.declarePublic('register')
    def register(self, obj):
        """See IUniqueIdSet.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            return histid_handler.register(obj)
    
    security.declareProtected(ManagePortal, 'unregister')
    def unregister(self, obj):
        """See IUniqueIdSet.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            histid_handler.unregister(obj)
    
    security.declarePublic('queryUid')
    def queryUid(self, obj, default=None):
        """See IUniqueIdQuery.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            return histid_handler.queryUid(obj, default)
    
    security.declarePublic('getUid')
    def getUid(self, obj):
        """See IUniqueIdQuery.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            return histid_handler.getUid(obj)
    
    security.declarePrivate('setUid')
    def setUid(self, obj, uid, check_uniqueness=True):
        """See IUniqueIdSet.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            return histid_handler.setUid(obj, uid, check_uniqueness)
    
    security.declarePublic('queryBrain')
    def queryBrain(self, uid, default=None):
        """See IUniqueIdBrainQuery.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            return histid_handler.queryBrain(uid, default)
    
    security.declarePublic('getBrain')
    def getBrain(self, uid):
        """See IUniqueIdBrainQuery.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            return histid_handler.getBrain(uid)
    
    security.declarePublic('getObject')
    def getObject(self, uid):
        """See IUniqueIdQuery.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            return histid_handler.getObject(uid)
    
    security.declarePublic('queryObject')
    def queryObject(self, uid, default=None):
        """See IUniqueIdQuery.
        """
        histid_handler = getToolByName(self, 'portal_historyidhandler', None)
        if histid_handler is not None:
            return histid_handler.queryObject(uid, default)
    
InitializeClass(UniqueIdHandlerTool)
