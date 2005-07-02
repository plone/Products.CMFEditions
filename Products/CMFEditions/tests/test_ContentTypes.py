import os, sys, time

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_base
from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase

PloneTestCase.setupPloneSite()
ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('PortalTransforms')
ZopeTestCase.installProduct('MimetypesRegistry')
ZopeTestCase.installProduct('CMFUid')
ZopeTestCase.installProduct('Zelenium')
ZopeTestCase.installProduct('PloneSelenium')
ZopeTestCase.installProduct('CMFEditions')

portal_owner = PloneTestCase.portal_owner
portal_name = PloneTestCase.portal_name
default_user = PloneTestCase.default_user

def setupCMFEditions(app, portal_name, quiet):
    portal = app[portal_name]
    start = time.time()
    if not quiet: ZopeTestCase._print('Adding CMFEdtions ... ')
    # Login as portal owner
    user = app.acl_users.getUserById(portal_owner).__of__(app.acl_users)
    newSecurityManager(None, user)
    if not hasattr(aq_base(portal), 'archetype_tool'):
        portal.portal_quickinstaller.installProduct('Archetypes')
    portal.portal_quickinstaller.installProduct('PloneSelenium')
    portal.portal_quickinstaller.installProduct('CMFEditions')
    # Log out
    noSecurityManager()
    get_transaction().commit()
    if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-start,))


ZopeTestCase.utils.appcall(setupCMFEditions, portal_name, quiet=0)


class TestPloneContents(PloneTestCase.PloneTestCase):

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
        portal_archivist = self.portal_archivist
        content = self.folder.doc
        content.text = 'text v1'
        content._editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='text/plain',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.text = 'text v2'
        content._editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        self.assertEqual(obj.text, 'text v1')
        self.metadata_test_one(obj)
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        self.assertEqual(obj.text, 'text v2')
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.text, 'text v1')
        self.metadata_test_one(content)

    def testNewsItem(self):
        self.folder.invokeFactory('News Item', id='news_one')
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = self.folder.news_one
        content.text = 'text v1'
        content._editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='text/plain',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.text = 'text v2'
        content._editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              format='text/plain',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        self.assertEqual(obj.text, 'text v1')
        self.metadata_test_one(obj)
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        self.assertEqual(obj.text, 'text v2')
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.text, 'text v1')
        self.metadata_test_one(content)

    def testImage(self):
        self.folder.invokeFactory('Image', id='image')
        img1 = open('img1.png', 'rb').read()
        img2 = open('img2.png', 'rb').read()
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = self.folder.image
        content.edit(file=img1)
        content._editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='image/png',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit(file=img2)
        content._editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              format='image/png',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        self.assertEqual(obj.data, img1)
        self.metadata_test_one(obj)
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        self.assertEqual(obj.data, img2)
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.data, img1)
        self.metadata_test_one(content)

    def testFile(self):
        self.folder.invokeFactory('File', id='file')
        file1 = open('img1.png', 'rb').read()
        file2 = open('img2.png', 'rb').read()
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = self.folder.file
        content.edit(file=file1)
        content._editMetadata(title='content',
                              subject=['content'],
                              description='content',
                              contributors='content',
                              format='image/png',
                              language='content',
                              rights='content',
                              )
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit(file=file2)
        content._editMetadata(title='contentOK',
                              subject=['contentOK'],
                              description='contentOK',
                              contributors='contentOK',
                              format='image/png',
                              language='contentOK',
                              rights='contentOK',
                              )
        portal_repository.save(content, comment='save no 2')
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        self.assertEqual(obj.data, file1)
        self.metadata_test_one(obj)
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        self.assertEqual(obj.data, file2)
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.data, file1)
        self.metadata_test_one(content)

    def testFolder(self):
        self.folder.invokeFactory('Folder', id='folder')
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = self.folder.folder
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
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        self.metadata_test_one(obj)
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.metadata_test_one(content)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPloneContents))
    return suite


if __name__ == '__main__':
    framework()
