from AccessControl.Permission import pname
from AccessControl.PermissionRole import PermissionRole
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ViewManagementScreens
from Products.CMFEditions.Modifiers import ConditionalModifier
from Products.CMFEditions.Modifiers import ConditionalTalesModifier
from Products.CMFEditions.StandardModifiers import AbortVersioningOfLargeFilesAndImages
from Products.CMFEditions.StandardModifiers import SkipVersioningOfLargeFilesAndImages

import unittest

CLASSES = (
    ConditionalModifier,
    ConditionalTalesModifier,
    AbortVersioningOfLargeFilesAndImages,
    SkipVersioningOfLargeFilesAndImages,
)


def permission_of(cls, name):
    """Return the permission protecting ``name`` on ``cls``, or None."""
    role = getattr(cls, f"{name}__roles__", None)
    if isinstance(role, PermissionRole):
        return role._p
    return None


class TestModifierSecurity(unittest.TestCase):
    def test_edit_requires_manage_portal(self):
        for cls in CLASSES:
            self.assertEqual(permission_of(cls, "edit"), pname(ManagePortal), cls)

    def test_accessors_require_view_management_screens(self):
        for cls in CLASSES:
            for name in ("isEnabled", "getModifier", "isApplicable", "isBroken"):
                self.assertEqual(
                    permission_of(cls, name), pname(ViewManagementScreens), (cls, name)
                )
        for cls in CLASSES[1:]:
            self.assertEqual(
                permission_of(cls, "getTalesCondition"),
                pname(ViewManagementScreens),
                cls,
            )
        for cls in CLASSES[2:]:
            self.assertEqual(
                permission_of(cls, "getFieldNames"),
                pname(ViewManagementScreens),
                cls,
            )

    def test_size_guard_internals_are_private(self):
        for cls in CLASSES[2:]:
            for name in (
                "getOnCloneModifiers",
                "beforeSaveModifier",
                "afterRetrieveModifier",
            ):
                role = getattr(cls, f"{name}__roles__", None)
                if (
                    name == "beforeSaveModifier"
                    and cls is AbortVersioningOfLargeFilesAndImages
                ):
                    continue  # not defined on this class
                self.assertFalse(isinstance(role, PermissionRole), (cls, name))
                self.assertEqual(tuple(role or ()), (), (cls, name))
