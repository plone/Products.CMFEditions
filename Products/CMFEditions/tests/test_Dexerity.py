# -*- coding: utf-8 -*-

import os

from Products.CMFEditions import PACKAGE_HOME
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_INTEGRATION_TESTING
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue


class TestDexterityContents(CMFEditionsBaseTestCase):

    layer = PLONE_APP_CONTENTTYPES_INTEGRATION_TESTING

    def afterSetUp(self):
        self.membership = self.portal.portal_membership
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow
        self.portal_repository = self.portal.portal_repository

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder = self.portal[self.portal.invokeFactory(
            "Folder",
            id='test-folder',
            title=u"Test Folder"
        )]

    def set_metadata(self, obj, text):
        obj.title = text
        obj.description = text

    def metadata_test(self, obj, text):
        self.assertEqual(obj.title.raw, text)
        self.assertEqual(obj.description, text)

    def testDocument(self):
        import pdb; pdb.set_trace()
        self.folder.invokeFactory('Document', id='doc')
        portal_repository = self.portal_repository
        # Create initial document
        content = self.folder.doc
        content.text = RichTextValue(
            u'têxt v1',
            'text/plain',
            'text/html'
        )
        self.set_metadata(content, 'content')
        portal_repository.applyVersionControl(content, comment='save no 1')
        # Update document
        content.text = RichTextValue(
            u'têxt v1',
            'text/plain',
            'text/html'
        )
        self.set_metadata(content, 'contentOK')
        portal_repository.save(content, comment='save no 2')
        # Test first revision
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.assertEqual(obj.text.raw, 'têxt v1')
        self.metadata_test(obj, 'content')
        # Test second revision
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.assertEqual(obj.text.raw, 'text v2')
        self.metadata_test(obj, 'contentOK')
        # Revert to first revision
        portal_repository.revert(content, 0)
        self.assertEqual(content.text.raw, 'têxt v1')
        self.metadata_test(content, 'content')
