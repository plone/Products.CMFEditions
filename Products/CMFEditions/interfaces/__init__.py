# -*- coding: utf-8 -*-
from zope import interface

from Products.CMFEditions.interfaces._tools import IArchivistTool  # noqa: F401
from Products.CMFEditions.interfaces._tools import IPortalModifierTool  # noqa: F401,E501
from Products.CMFEditions.interfaces._tools import IPurgePolicyTool  # noqa: F401,E501
from Products.CMFEditions.interfaces._tools import IStorageTool  # noqa: F401


class IVersioned(interface.Interface):
    """Marker interface for objects that carry a version id, and are
    thus versioned.
    """
    version_id = interface.Attribute('The version id of this object.')
