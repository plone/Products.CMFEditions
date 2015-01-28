# -*- coding: utf-8 -*-
#

from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase

import os
from Products.CMFEditions import PACKAGE_HOME

class TestPloneContents(CMFEditionsBaseTestCase):

    def afterSetUp(self):
        self.membership = self.portal.portal_membership
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow
        self.portal_repository = self.portal.portal_repository
        self.portal_archivist = self.portal.portal_archivist

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
        content.edit('text/plain','text v1')
        content.editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='text/plain',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit('text/plain','text v2')
        content.editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              format='text/plain',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.EditableBody(), 'text v1')
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.EditableBody(), 'text v2')
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.EditableBody(), 'text v1')
        self.metadata_test_one(content)

    def testNewsItem(self):
        self.folder.invokeFactory('News Item', id='news_one')
        portal_repository = self.portal_repository
        content = self.folder.news_one
        content.edit('text v1', text_format='text/plain')
        content.editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='text/plain',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit('text v2', text_format='text/plain')
        content.editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              format='text/plain',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.EditableBody(), 'text v1')
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.EditableBody(), 'text v2')
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.EditableBody(), 'text v1')
        self.metadata_test_one(content)

    def testImage(self):
        self.folder.invokeFactory('Image', id='image')
        portal_repository = self.portal_repository
        img1 = open(os.path.join(PACKAGE_HOME, 'tests/images/img1.png'), 'rb').read()
        img2 = open(os.path.join(PACKAGE_HOME, 'tests/images/img2.png'), 'rb').read()
        content = self.folder.image
        content.edit(file=img1)
        content.editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='image/png',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit(file=img2)
        content.editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              format='image/png',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.data, img1)
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.data, img2)
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.data, img1)
        self.metadata_test_one(content)

    def testFile(self):
        self.folder.invokeFactory('File', id='file')
        file1 = open(os.path.join(PACKAGE_HOME, 'tests/images/img1.png'), 'rb').read()
        file2 = open(os.path.join(PACKAGE_HOME, 'tests/images/img2.png'), 'rb').read()
        portal_repository = self.portal_repository
        content = self.folder.file
        content.edit(file=file1)
        content.editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='image/png',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit(file=file2)
        content.editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              format='image/png',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.data, file1)
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.data, file2)
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.data, file1)
        self.metadata_test_one(content)

    def testFolder(self):
        self.folder.invokeFactory('Image', id='folder')
        portal_repository = self.portal_repository
        content = self.folder.folder
        # Use private method because webDAV locking is tripping this up
        # using the public method and ATCT
        content._editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='image/png',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content._editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              format='image/png',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        obj = portal_repository.retrieve(content, 0).object
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.metadata_test_one(content)
