# -*- coding: utf-8 -*-
#########################################################################
# Copyright (c) 2008 Alberto Berti, Gregoire Weber.
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
"""Event Subscribers

$Id: ArchivistTool.py,v 1.15 2005/06/24 11:34:08 gregweb Exp $
"""
from zope.i18nmessageid import MessageFactory
from Acquisition import aq_get

from Products.CMFEditions.utilities import isObjectChanged, maybeSaveVersion
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError
from Products.CMFEditions import CMFEditionsMessageFactory as _

PMF = MessageFactory('plone')

def webdavObjectEventHandler(obj, event, comment):
    obj = event.object

    changed = isObjectChanged(obj)

    if not changed:
        return

    try:
        maybeSaveVersion(obj, comment=comment, force=False)
    except FileTooLargeToVersionError:
        pass # There's no way to emit a warning here. Or is there?

def webdavObjectInitialized(obj, event):
    return webdavObjectEventHandler(obj, event, comment=_('Initial revision (WebDAV)'))

def webdavObjectEdited(obj, event):
    return webdavObjectEventHandler(obj, event, comment=_('Edited (WebDAV)'))

def _getVersionComment(object):
    request = aq_get(object, 'REQUEST', None)
    return request and request.get('cmfeditions_version_comment', '')

def objectInitialized(obj, event):
    comment = _getVersionComment(event.object) or _('Initial revision')
    return webdavObjectEventHandler(obj, event, comment=comment)

def objectEdited(obj, event):
    comment = _getVersionComment(event.object) or PMF('Edited')
    return webdavObjectEventHandler(obj, event, comment=comment)
