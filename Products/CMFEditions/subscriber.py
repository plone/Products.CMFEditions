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

from Products.CMFEditions.utilities import isObjectChanged, maybeSaveVersion
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError

def webdavObjectEventHandler(event, comment):
    obj = event.object

    changed = isObjectChanged(obj)

    if not changed:
        return

    try:
        maybeSaveVersion(obj, comment=comment, force=False)
    except FileTooLargeToVersionError:
        pass # There's no way to emit a warning here. Or is there?

def webdavObjectInitialized(event):
    return webdavObjectEventHandler(event, comment='Initial revision')

def webdavObjectEdited(event):
    return webdavObjectEventHandler(event, comment='Edited (WebDAV)')
