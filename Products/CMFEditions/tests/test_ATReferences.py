# -*- coding: utf-8 -*-

from Products.CMFEditions.tests.base import CMFEditionsATBaseTestCase


class TestATReferences(CMFEditionsATBaseTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])

        # add an additional user
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')

        # add a folder with two documents in it
        self.portal.invokeFactory('Folder', 'fol')
        self.portal.fol.invokeFactory('Document', 'doc1')
        self.portal.fol.invokeFactory('Document', 'doc2')

    def test_referencesDataGetSavedAndRestored(self):
        # this case checks restoring a version with a reference to
        # a working copy with no reference
        repo = self.portal.portal_repository
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        repo.applyVersionControl(doc1)
        repo.applyVersionControl(doc2)
        relationship = 'dumb_relationship'
        doc1.addReference(doc2, relationship=relationship)
        doc1.setTitle('v1')
        repo.save(doc1)
        from Products.Archetypes.config import REFERENCE_ANNOTATION as \
             refs_container_name
        refs = getattr(doc1, refs_container_name).objectValues()
        doc1.deleteReference(doc2)
        should_be_empty_now = getattr(doc1, refs_container_name).objectValues()
        self.assertFalse(should_be_empty_now)
        repo.revert(doc1, 1)
        after_retrieve_refs = getattr(doc1, refs_container_name).objectValues()
        self.assertEqual(refs[0].targetUID, after_retrieve_refs[0].targetUID)
        self.assertEqual(refs[0].sourceUID, after_retrieve_refs[0].sourceUID)
        self.assertEqual(refs[0].relationship,
                         after_retrieve_refs[0].relationship)

    def test_referencesAreSavedAndRestored(self):
        # this case checks restoring a version with a reference to
        # a working copy with no reference

        repo = self.portal.portal_repository
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        repo.applyVersionControl(doc1)
        repo.applyVersionControl(doc2)

        doc1.addReference(doc2)
        doc1.setTitle('v1')
        repo.save(doc1)
        doc1.deleteReference(doc2)
        self.assertFalse(doc1.getReferences(targetObject=doc2))
        repo.revert(doc1, 1)
        self.assertEqual(doc1.getReferences(targetObject=doc2), [doc2])

    def test_referencesDataGetSavedAndRestored2(self):
        # this case checks restoring a version with no refs, to a workin copy
        # with a ref, without using RetainATRefs

        repo = self.portal.portal_repository
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        repo.applyVersionControl(doc1)
        repo.applyVersionControl(doc2)
        doc1.setTitle('v1')
        repo.save(doc1)
        relationship = 'dumb_relationship'
        doc1.addReference(doc2, relationship=relationship)
        doc1.setTitle('v2')
        from Products.Archetypes.config import REFERENCE_ANNOTATION
        repo.revert(doc1, 1)
        should_be_empty_now = getattr(doc1, REFERENCE_ANNOTATION).objectValues()
        self.assertFalse(should_be_empty_now)

    def test_referencesAreSavedAndRestored2(self):
        # this case checks restoring a version with no refs, to a workin copy
        # with a ref, without using RetainATRefs

        repo = self.portal.portal_repository
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        repo.applyVersionControl(doc1)
        repo.applyVersionControl(doc2)

        doc1.setTitle('v1')
        repo.save(doc1)
        doc1.addReference(doc2)
        self.assertEqual(doc1.getReferences(targetObject=doc2), [doc2])
        repo.revert(doc1, 1)
        self.assertFalse(doc1.getReferences(targetObject=doc2))
        # The above does not fail because ReferenceCatalog.getReferences calls
        # _resolveBrains after a catalog query to get the reference objects - so
        # the returned list is empty. But the reference_catalog still has the reference
        # indexed:
        rc = self.portal.reference_catalog
        self.assertFalse(rc(sourceUID=doc1.UID()))



    def test_contentReferencesAreSavedAndRestored(self):
        repo = self.portal.portal_repository
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        repo.applyVersionControl(doc1)
        repo.applyVersionControl(doc2)

#  XXX Simply using this kind of ref doesn't work
#         from Products.Archetypes.ReferenceEngine import ContentReference
#         doc1.addReference(doc2, referenceClass=ContentReference,
#         contentType='Document')
#         doc1.setTitle('v1')
#         ref_doc = doc1.getReferenceImpl(targetObject=doc2)[0]
#         ref_doc.setTitle('ref_doc v1')
#         repo.save(doc1)
#         doc1.deleteReference(doc2)
#         self.assertFalse(doc1.getReferences(targetObject=doc2))
#         repo.revert(doc1, 1)
#         self.assertEqual(aq_base(doc1.getReferences(targetObject=doc2)[0]),
#                          aq_base(doc2))
#         ref_doc = doc1.getReferenceImpl(targetObject=doc2)[0]
#         self.assertEqual('ref_doc v1', ref_doc.getTitle())

    def test_referencesAreDeleted(self):

        repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        repo.applyVersionControl(doc1)
        repo.applyVersionControl(doc2)

        doc1.addReference(doc2)
        doc1.setTitle('v1')
        repo.save(doc1)
        fol.manage_delObjects('doc2')
        repo.revert(doc1, 1)
        self.assertEqual(doc1.getReferences(), [])
        self.assertFalse(doc1.getReferenceImpl())

    def test_refcatalogIsUpdatedWithInsideRefsAndATRefsBetweenChildrenObjs(self):

        repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2

        # just configure the standard folder to treat the childrens as
        # inside refrences. For this we reconfigure the standard modifiers.
        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")
        repo.applyVersionControl(fol)
        doc1.setTitle('v1')
        doc1.addReference(doc2)
        doc2.addReference(doc1)
        repo.save(fol)

        doc1.setTitle('changed')
        doc1.deleteReference(doc2)
        doc2.deleteReference(doc1)
        self.assertFalse(doc1.getReferences())
        self.assertFalse(doc2.getReferences())
        repo.revert(fol, 1)

        doc1 = self.portal.fol.doc1
        doc2 = self.portal.fol.doc2
        self.assertEqual(doc1.Title(), 'v1')
        self.assertEqual([doc1], doc2.getReferences())
        self.assertEqual([doc2], doc1.getReferences())

    def test_refOnWorkingCopyArePreserved(self):
        repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = self.portal.fol.doc1
        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("RetainATRefs",
                             enabled=True,
                             condition="python: True")
        repo.applyVersionControl(doc1)
        doc1.addReference(fol)
        repo.save(doc1)
        repo.revert(doc1, 1)
        self.assertEqual([fol], doc1.getReferences())
