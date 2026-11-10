"""Test the @@check-modifier-conditions view."""

from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.protect.authenticator import createToken
from Products.CMFEditions.browser.modifiers import DEFAULT_CONDITIONS
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase
from zExceptions import BadRequest
from zExceptions import Forbidden
from zExceptions import Unauthorized
from zope.component import getMultiAdapter


class TestCheckModifierConditions(CMFEditionsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.tool = self.portal.portal_modifier

    def get_view(self):
        return getMultiAdapter(
            (self.portal, self.request), name="check-modifier-conditions"
        )

    def post(self, **form):
        self.request.method = "POST"
        self.request.form.update(form)
        return self.get_view()()

    def change(self, modifier_id, condition="python: False"):
        self.tool[modifier_id].edit(condition=condition)

    def test_default_conditions(self):
        html = self.get_view()()
        for modifier_id in self.tool.objectIds():
            self.assertIn(modifier_id, html)
        # RetainUIDs has no condition.
        self.assertIn("no condition", html)
        self.assertIn("using default condition", html)
        self.assertNotIn("Current condition", html)
        self.assertNotIn("Revert", html)
        self.assertNotIn("_authenticator", html)
        # Nothing in the main_template.
        self.assertNotIn("portal-header", html)

    def test_changed_condition(self):
        self.change("SkipParentPointers")
        html = self.get_view()()
        self.assertIn("Default condition", html)
        self.assertIn("<code>python: True</code>", html)
        self.assertIn("<code>python: False</code>", html)
        self.assertIn('value="SkipParentPointers"', html)
        self.assertIn('name="_authenticator"', html)
        self.assertIn("Revert to default condition", html)
        self.assertIn("Revert all to default conditions", html)

    def test_revert_one(self):
        self.change("SkipParentPointers")
        self.change("Skip_z3c_blobfile")
        html = self.post(
            revert="1", modifier_id="SkipParentPointers", _authenticator=createToken()
        )
        self.assertIn("Reverted condition of SkipParentPointers.", html)
        self.assertEqual(
            self.tool.SkipParentPointers.getTalesCondition(),
            DEFAULT_CONDITIONS["SkipParentPointers"],
        )
        self.assertEqual(
            self.tool.Skip_z3c_blobfile.getTalesCondition(), "python: False"
        )

    def test_revert_all(self):
        self.change("SkipParentPointers")
        self.change("AbortVersioningOfLargeFilesAndImages")
        html = self.post(revert_all="1", _authenticator=createToken())
        self.assertIn("Reverted condition of SkipParentPointers.", html)
        self.assertIn(
            "Reverted condition of AbortVersioningOfLargeFilesAndImages.", html
        )
        self.assertNotIn("Revert all", html)
        for modifier_id, condition in DEFAULT_CONDITIONS.items():
            self.assertEqual(
                self.tool[modifier_id].getTalesCondition(), condition, modifier_id
            )

    def test_revert_keeps_enabled_and_title(self):
        # SkipParentPointers is enabled by default, SkipVersioningOfLargeFilesAndImages not.
        for modifier_id, enabled in (
            ("SkipParentPointers", True),
            ("SkipVersioningOfLargeFilesAndImages", False),
        ):
            modifier = self.tool[modifier_id]
            title = "My title"
            modifier.edit(enabled=enabled, condition="python: False", title=title)
            self.assertEqual(bool(modifier.isEnabled()), enabled)
            self.post(revert="1", modifier_id=modifier_id, _authenticator=createToken())
            self.assertEqual(
                modifier.getTalesCondition(), DEFAULT_CONDITIONS[modifier_id]
            )
            self.assertEqual(bool(modifier.isEnabled()), enabled, modifier_id)
            self.assertEqual(modifier.title, title, modifier_id)

    def test_revert_unknown(self):
        html = self.post(
            revert="1", modifier_id="RetainUIDs", _authenticator=createToken()
        )
        self.assertIn("Cannot revert condition of RetainUIDs.", html)
        html = self.post(revert="1", modifier_id="foo", _authenticator=createToken())
        self.assertIn("Cannot revert condition of foo.", html)

    def test_revert_requires_authenticator(self):
        self.change("SkipParentPointers")
        with self.assertRaises(Forbidden):
            self.post(revert="1", modifier_id="SkipParentPointers")
        with self.assertRaises(Forbidden):
            self.post(revert_all="1", _authenticator="wrong")
        self.assertEqual(
            self.tool.SkipParentPointers.getTalesCondition(), "python: False"
        )

    def test_revert_requires_post(self):
        self.change("SkipParentPointers")
        self.request.form.update(
            revert="1", modifier_id="SkipParentPointers", _authenticator=createToken()
        )
        with self.assertRaises(BadRequest):
            self.get_view()()
        self.assertEqual(
            self.tool.SkipParentPointers.getTalesCondition(), "python: False"
        )

    def test_permission(self):
        # The view is protected with cmf.ManagePortal.
        setRoles(self.portal, TEST_USER_ID, ["Site Administrator"])
        with self.assertRaises(Unauthorized):
            self.portal.restrictedTraverse("@@check-modifier-conditions")
        logout()
        with self.assertRaises(Unauthorized):
            self.portal.restrictedTraverse("@@check-modifier-conditions")

    def test_manager_can_traverse(self):
        view = self.portal.restrictedTraverse("@@check-modifier-conditions")
        self.assertIn("using default condition", view())

    def test_not_on_content(self):
        self.portal.invokeFactory("Document", "doc")
        with self.assertRaises(AttributeError):
            self.portal.doc.restrictedTraverse("@@check-modifier-conditions")

    def test_without_plone_protect(self):
        from Products.CMFEditions.browser import modifiers
        from unittest import mock

        self.change("SkipParentPointers")
        with (
            mock.patch.object(modifiers, "CheckAuthenticator", None),
            mock.patch.object(modifiers, "queryMultiAdapter", return_value=None),
        ):
            html = self.get_view()()
            self.assertIn("Revert to default condition", html)
            self.assertNotIn("_authenticator", html)
            html = self.post(revert="1", modifier_id="SkipParentPointers")
        self.assertIn("Reverted condition of SkipParentPointers.", html)
