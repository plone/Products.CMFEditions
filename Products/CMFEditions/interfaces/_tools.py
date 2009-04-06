# -*- coding: utf-8 -*-
from zope.interface import Interface


class IArchivistTool(Interface):
    """Marker interface for the portal_archivist tool.
    """


class IPortalModifierTool(Interface):
    """Marker interface for the portal_modifier tool.
    """


class IPurgePolicyTool(Interface):
    """Marker interface for the portal_purgepolicy tool.
    """


class IStorageTool(Interface):
    """Marker interface for the portal_historiesstorage tool.
    """
