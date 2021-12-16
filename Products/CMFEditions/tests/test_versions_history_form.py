#########################################################################
# Copyright (c) 2004, 2005 Alberto Berti, Gregoire Weber.
# Reflab (Vincenzo Di Somma, Francesco Ciriaci, Riccardo Lemmi)
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
"""Test the versions_history_form template."""

from plone.app.textfield.value import RichTextValue
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase
from Products.Five.browser import BrowserView
from zope.component import provideAdapter
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserView


_TEXT_INITIAL = "Initial text."
_TEXT_NEW = "New text."


class TestVersionsHistoryForm(CMFEditionsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.portal_repository = self.portal.portal_repository
        self.portal.invokeFactory(
            "Document",
            "doc",
            title="Document 1",
            text=RichTextValue(_TEXT_INITIAL, "text/plain", "text/plain"),
        )
        self.doc = self.portal.doc
        self.portal_repository.applyVersionControl(self.doc, comment="save version 0")
        self.request = self.portal.REQUEST

    def test_versions_history_form(self):
        self.doc.text = RichTextValue(_TEXT_NEW, "text/plain", "text/plain")
        self.portal_repository.save(self.doc, comment="save version 1")

        html = self._render_versions_history_form(item=self.doc, version_id="0")
        self.assertTrue(_TEXT_INITIAL in html)
        self.assertFalse(_TEXT_NEW in html)

        html = self._render_versions_history_form(item=self.doc, version_id="1")
        self.assertFalse(_TEXT_INITIAL in html)
        self.assertTrue(_TEXT_NEW in html)

    def test_versions_history_form_custom_version_view(self):
        """Assert that if we define an @@version-view then it will be used to
        display the versions.
        """
        dummy_str = "Blah"

        class DummyVersionView(BrowserView):
            def __call__(self):
                return dummy_str

        provideAdapter(
            factory=DummyVersionView,
            adapts=(Interface, Interface),
            provides=IBrowserView,
            name="version-view",
        )

        html = self._render_versions_history_form(item=self.doc, version_id="0")
        self.assertTrue(dummy_str in html)
        self.assertFalse(_TEXT_INITIAL in html)

    def _render_versions_history_form(self, item, version_id):
        self.request["version_id"] = version_id
        return item.unrestrictedTraverse("versions_history_form")()
