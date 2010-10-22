# -*- coding: utf-8 -*-
from zope import interface

from _tools import IArchivistTool
from _tools import IPortalModifierTool
from _tools import IPurgePolicyTool
from _tools import IStorageTool


class IVersioned(interface.Interface):
    """Marker interface for objects that carry a version id, and are
    thus versioned.
    """
    version_id = interface.Attribute('The version id of this object.')

