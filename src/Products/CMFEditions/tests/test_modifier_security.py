from AccessControl.Permission import pname
from AccessControl.PermissionRole import PermissionRole
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ViewManagementScreens
from Products.CMFEditions.Modifiers import ConditionalModifier
from Products.CMFEditions.Modifiers import ConditionalTalesModifier
from Products.CMFEditions.StandardModifiers import (
    AbortVersioningOfLargeFilesAndImages,
)
from Products.CMFEditions.StandardModifiers import (
    SkipVersioningOfLargeFilesAndImages,
)
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase

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
                if name == "beforeSaveModifier" and cls is AbortVersioningOfLargeFilesAndImages:
                    continue  # not defined on this class
                self.assertFalse(
                    isinstance(role, PermissionRole), (cls, name)
                )
                self.assertEqual(tuple(role or ()), (), (cls, name))


class TestModifierEditForm(CMFEditionsBaseTestCase):
    """Submitting the edit form with a REQUEST must render the form again."""

    def _check(self, modifier_id, **kwargs):
        modifier = self.portal.portal_modifier[modifier_id]
        result = modifier.edit(REQUEST=self.request, **kwargs)
        self.assertIsInstance(result, str, modifier_id)
        self.assertIn("Edit Modifier", result, modifier_id)
        self.assertEqual(self.request.get("manage_tabs_message"), "Changed")
        return modifier

    def test_conditional_tales_modifier_edit_returns_html(self):
        modifier = self._check(
            "OMInsideChildrensModifier", enabled=True, condition="python:True"
        )
        self.assertEqual(modifier.getTalesCondition(), "python:True")

    def test_abort_large_files_edit_returns_html(self):
        modifier = self._check(
            "AbortVersioningOfLargeFilesAndImages", max_size="1000", field_names="foo"
        )
        self.assertEqual(modifier.max_size, 1000)
        self.assertEqual(modifier.field_names, ("foo",))

    def test_skip_large_files_edit_returns_html(self):
        modifier = self._check(
            "SkipVersioningOfLargeFilesAndImages", max_size="1000", field_names="foo"
        )
        self.assertEqual(modifier.max_size, 1000)
        self.assertEqual(modifier.field_names, ("foo",))
