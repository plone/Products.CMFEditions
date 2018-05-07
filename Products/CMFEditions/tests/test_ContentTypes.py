# -*- coding: utf-8 -*-

from plone.app.textfield.value import RichTextValue
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from Products.CMFEditions import PACKAGE_HOME
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase
from Products.CMFPlone.utils import _createObjectByType
import os


class TestPloneContents(CMFEditionsBaseTestCase):

    def afterSetUp(self):
        self.membership = self.portal.portal_membership
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow
        self.portal_repository = self.portal.portal_repository
        self.portal_archivist = self.portal.portal_archivist
        _createObjectByType('Folder', self.portal, id='folder')
        self.folder = self.portal.folder

    def getPermissionsOfRole(self, role):
        perms = self.portal.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]

    def metadata_test_one(self, obj):
        self.assertEqual(obj.Title(), 'content')
        self.assertEqual(obj.Subject(), ('content',))
        self.assertEqual(obj.Description(), 'content')
        self.assertEqual(obj.Contributors(), ('content',))
        self.assertEqual(obj.Language(), 'content')
        self.assertEqual(obj.Rights(), 'content')

    def metadata_test_two(self, obj):
        self.assertEqual(obj.Title(), 'contentOK')
        self.assertEqual(obj.Subject(), ('contentOK',))
        self.assertEqual(obj.Description(), 'contentOK')
        self.assertEqual(obj.Contributors(), ('contentOK',))
        self.assertEqual(obj.Language(), 'contentOK')
        self.assertEqual(obj.Rights(), 'contentOK')

    def testDocument(self):
        self.folder.invokeFactory('Document', id='doc')
        portal_repository = self.portal_repository
        content = self.folder.doc
        content.text = RichTextValue(u'text v1', 'text/plain', 'text/plain')
        content.title = u'content'
        content.subject = [u'content']
        content.description = u'content'
        content.contributors = [u'content']
        content.language = 'content'
        content.rights = u'content'
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.text = RichTextValue(u'text v2', 'text/plain', 'text/plain')
        content.title = u'contentOK'
        content.subject = [u'contentOK']
        content.description = u'contentOK'
        content.contributors = [u'contentOK']
        content.language = 'contentOK'
        content.rights = u'contentOK'
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.text.raw, 'text v1')
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.text.raw, 'text v2')
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.text.raw, 'text v1')
        self.metadata_test_one(content)

    def testNewsItem(self):
        self.folder.invokeFactory('News Item', id='news_one')
        portal_repository = self.portal_repository
        content = self.folder.news_one
        content.text = RichTextValue(u'text v1', 'text/plain', 'text/plain')
        content.title = u'content'
        content.subject = [u'content']
        content.description = u'content'
        content.contributors = [u'content']
        content.language = 'content'
        content.rights = u'content'
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.text = RichTextValue(u'text v2', 'text/plain', 'text/plain')
        content.title = u'contentOK'
        content.subject = [u'contentOK']
        content.description = u'contentOK'
        content.contributors = [u'contentOK']
        content.language = 'contentOK'
        content.rights = u'contentOK'
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.text.raw, 'text v1')
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.text.raw, 'text v2')
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.text.raw, 'text v1')
        self.metadata_test_one(content)

    def testImage(self):
        self.folder.invokeFactory('Image', id='image')
        portal_repository = self.portal_repository
        img1 = open(os.path.join(PACKAGE_HOME, 'tests/images/img1.png'), 'rb').read()
        img2 = open(os.path.join(PACKAGE_HOME, 'tests/images/img2.png'), 'rb').read()
        content = self.folder.image
        content.image = NamedBlobImage(img1, u'img1.png', u'image/png')
        content.title = u'content'
        content.subject = [u'content']
        content.description = u'content'
        content.contributors = [u'content']
        content.language = 'content'
        content.rights = u'content'
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.image = NamedBlobImage(img2, u'img2.png', u'image/png')
        content.title = u'contentOK'
        content.subject = [u'contentOK']
        content.description = u'contentOK'
        content.contributors = [u'contentOK']
        content.language = 'contentOK'
        content.rights = u'contentOK'
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.image.data, img1)
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.image.data, img2)
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.image.data, img1)
        self.metadata_test_one(content)

    def testFile(self):
        self.folder.invokeFactory('File', id='file')
        file1 = open(os.path.join(PACKAGE_HOME, 'tests/images/img1.png'), 'rb').read()
        file2 = open(os.path.join(PACKAGE_HOME, 'tests/images/img2.png'), 'rb').read()
        portal_repository = self.portal_repository
        content = self.folder.file
        content.file = NamedBlobFile(file1, u'img1.png', u'image/png')
        content.title = u'content'
        content.subject = [u'content']
        content.description = u'content'
        content.contributors = [u'content']
        content.language = 'content'
        content.rights = u'content'
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.file = NamedBlobImage(file2, u'img2.png', u'image/png')
        content.title = u'contentOK'
        content.subject = [u'contentOK']
        content.description = u'contentOK'
        content.contributors = [u'contentOK']
        content.language = 'contentOK'
        content.rights = u'contentOK'
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.file.data, file1)
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.file.data, file2)
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.file.data, file1)
        self.metadata_test_one(content)

    def testFolder(self):
        self.folder.invokeFactory('Image', id='folder')
        portal_repository = self.portal_repository
        content = self.folder.folder
        content.title = u'content'
        content.subject = [u'content']
        content.description = u'content'
        content.contributors = [u'content']
        content.language = 'content'
        content.rights = u'content'
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.title = u'contentOK'
        content.subject = [u'contentOK']
        content.description = u'contentOK'
        content.contributors = [u'contentOK']
        content.language = 'contentOK'
        content.rights = u'contentOK'
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.metadata_test_one(content)
