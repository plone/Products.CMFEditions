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
"""Utilities

$Id: utilities.py,v 1.1 2005/01/06 14:25:44 gregweb Exp $
"""

from Persistence import Persistent

class KwAsAttributes(Persistent):
    """Class attaching to itself passed keyword attributes.
    """
    def __init__(self, **kw):
        for key, val in kw.items():
            setattr(self, key, val)
