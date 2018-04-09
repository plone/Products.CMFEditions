# -*- coding: utf-8 -*-
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
"""Manages Reference Factories.

"""

from zope.interface import Interface


class IReferenceFactories(Interface):
    """Contains Factories knowing how and where to instantiate an object.

    Caution:

    - This interface is in flux and probably will change when implementing
      Archteypes reference support.
    - The source parameter will disappear as soon as on save the back
      references are save with the object.
    """

    def invokeFactory(repo_clone, source, selector=None):
        """Invokes the right factory for the object in a history.

        Returns the attached object and it's id.
        """

    def hasBeenMoved(obj, source):
        """Returns True if the object has been moved away from ``source``.
        """
