 
import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Interface.Verify import verifyObject
from Acquisition import aq_base

from OFS.ObjectManager import UNIQUE, REPLACEABLE

from Products.CMFEditions.interfaces.IRepository \
     import ICopyModifyMergeRepository

from Products.PloneTestCase import PloneTestCase
from Products.CMFEditions.tests import installProduct

PloneTestCase.setupPloneSite()
ZopeTestCase.installProduct('CMFUid')
ZopeTestCase.installProduct('CMFEditions')

ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('PortalTransforms')
ZopeTestCase.installProduct('MimetypesRegistry')
ZopeTestCase.installProduct('ATContentTypes')

portal_owner = PloneTestCase.portal_owner
portal_name = PloneTestCase.portal_name
default_user = PloneTestCase.default_user

class TestATReferences(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])
        installProduct(self.portal, 'CMFEditions')

        # add an additional user
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')
        
        # add a folder with two documents in it
        self.portal.invokeFactory('Folder', 'fol')
        self.portal.fol.invokeFactory('Document', 'doc1')
        self.portal.fol.invokeFactory('Document', 'doc2')

    def test_referencesDataGetSavedAndRestored(self):

        repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        repo.applyVersionControl(doc1)
        repo.applyVersionControl(doc2)

        doc1.addReference(doc2)
        doc1.setTitle('v1')
        repo.save(doc1)
        from Products.Archetypes.config import REFERENCE_ANNOTATION as refs_container_name
        refs = getattr(doc1, refs_container_name).objectValues()
        doc1.deleteReference(doc2)
        should_be_empty_now = getattr(doc1, refs_container_name).objectValues()
        self.failIf(should_be_empty_now)
        repo.revert(doc1, 1)
        after_retrieve_refs = getattr(doc1, refs_container_name).objectValues()
        self.assertEqual(refs[0].targetUID, after_retrieve_refs[0].targetUID)
        self.assertEqual(refs[0].sourceUID, after_retrieve_refs[0].sourceUID)

    def test_referencesAreRestored(self):

        repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        repo.applyVersionControl(doc1)
        repo.applyVersionControl(doc2)

        doc1.addReference(doc2)
        doc1.setTitle('v1')
        repo.save(doc1)
        doc1.deleteReference(doc2)
        self.failIf(doc1.getReferences(targetObject=doc2))
        repo.revert(doc1, 1)
        self.failUnless(doc1.getReferences(targetObject=doc2))


if __name__ == '__main__':
    framework()
else:
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestIntegration))
        return suite
