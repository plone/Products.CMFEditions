from Products.CMFEditions.interfaces._tools import IArchivistTool  # noqa: F401
from Products.CMFEditions.interfaces._tools import IPortalModifierTool  # noqa: F401
from Products.CMFEditions.interfaces._tools import IPurgePolicyTool  # noqa: F401
from Products.CMFEditions.interfaces._tools import IStorageTool  # noqa: F401
from zope import interface


class IVersioned(interface.Interface):
    """Marker interface for objects that carry a version id, and are
    thus versioned.
    """

    version_id = interface.Attribute("The version id of this object.")
