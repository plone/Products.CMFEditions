# -*- coding: utf-8 -*-
# Tests which use the FAQ 'product' in this folder.
# This is a folderish content type which also uses references.
#
# Nastily patch Products to get FAQ accepted
import os
import Products
Products.__path__.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Products.PloneTestCase import PloneTestCase

# We may not have Archetypes, which the FAQ tests require
try:
    PloneTestCase.installProduct('FAQ')
    PloneTestCase.setupPloneSite(products=('FAQ', ))
    HAS_AT = True
except ImportError:
    HAS_AT = False

from Products.CMFEditions import PACKAGE_HOME

class TestATContents(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.membership = self.portal.portal_membership
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow
        self.portal_repository = self.portal.portal_repository
        self.portal_archivist = self.portal.portal_archivist
        self.folder.manage_permission('Add FAQ content', ['Member', 'Manager'])

    def set_metadata(self, obj, text):
        obj.setTitle(text + ' title')
        obj.setSubject(text + ' subject')
        obj.setDescription(text + ' description')
        obj.setContributors(text + ' contributors')
        obj.setLanguage(text + ' language')
        obj.setRights(text + ' rights')

    def metadata_test(self, obj, text):
        self.assertEqual(obj.Title(), text + ' title')
        self.assertEqual(obj.Subject(), (text + ' subject',))
        self.assertEqual(obj.Description(), text + ' description')
        self.assertEqual(obj.Contributors(), (text + ' contributors',))
        self.assertEqual(obj.Language(), text + ' language')
        self.assertEqual(obj.Rights(), text + ' rights')

    def getPermissionsOfRole(self, role):
        perms = self.portal.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]

    def setFAQ(self, content, tag):
        content.setSummary('summary '+tag)
        content.setIntroduction('intro '+tag)
        content.setSections(('sections '+tag+' 1', 'sections '+tag+' 2'))
        self.set_metadata(content, 'content '+tag)

    def verifyFAQ(self, content, tag):
        self.assertEqual(content.getSummary(), 'summary '+tag)
        self.assertEqual(content.getIntroduction(), 'intro '+tag)
        self.assertEqual(content.getSections(), ('sections '+tag+' 1', 'sections '+tag+' 2'))
        self.metadata_test(content, 'content '+tag)

    def testFAQ(self):
        self.folder.invokeFactory('FAQ', id='test_faq')
        portal_repository = self.portal_repository
        content = self.folder.test_faq
        self.setFAQ(content, 'v1')
        portal_repository.applyVersionControl(content, comment='save no 1')
        self.setFAQ(content, 'v2')
        portal_repository.save(content, comment='save no 2')
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.verifyFAQ(obj, 'v1')
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.verifyFAQ(obj, 'v2')
        portal_repository.revert(content, 0)
        self.verifyFAQ(content, 'v1')

    def setQuestion(self, question, tag):
        question.setSection('section '+tag)
        question.setTitle('title '+tag)
        question.setAnswer('answer '+tag)

    def verifyQuestion(self, question, tag):
        self.assertEqual(question.getSection(), 'section '+tag)
        self.assertEqual(question.getTitle(), 'title '+tag)
        self.assertEqual(question.getAnswer(), 'answer '+tag)

    def testFAQWithContent(self):
        self.folder.invokeFactory('FAQ', id='test_faq')
        portal_repository = self.portal_repository
        faq = self.folder.test_faq
        self.setFAQ(faq, 'v1')
        for id in ('q1', 'q2'):
            faq.invokeFactory('FAQQuestion', id=id)
            question = getattr(faq, id)
            self.setQuestion(question, id+' v1')

        portal_repository.applyVersionControl(faq, comment='save no 1')
        self.setFAQ(faq, 'v2')
        for id in ('q1', 'q2'):
            question = getattr(faq, id)
            self.setQuestion(question, id+' v2')
        portal_repository.save(faq, comment='save no 2')

        vdata = portal_repository.retrieve(faq, 0)
        obj = vdata.object
        self.verifyFAQ(obj, 'v1')
        for id in ('q1', 'q2'):
            question = getattr(obj, id)
            self.verifyQuestion(question, id+' v1')

        vdata = portal_repository.retrieve(faq, 1)
        obj = vdata.object
        self.verifyFAQ(obj, 'v2')
        for id in ('q1', 'q2'):
            question = getattr(obj, id)
            self.verifyQuestion(question, id+' v2')

        for id in ('q1', 'q2'):
            question = getattr(faq, id)
            self.verifyQuestion(question, id+' v2')
        portal_repository.revert(faq, 0)
        self.verifyFAQ(faq, 'v1')
        for id in ('q1', 'q2'):
            question = getattr(faq, id)
            self.verifyQuestion(question, id+' v1')

    def createImage(self, id='image'):
        self.folder.invokeFactory('Image', id=id)
        img1 = open(os.path.join(PACKAGE_HOME, 'tests/images/img1.png'), 'rb').read()
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = getattr(self.folder, id)
        content.edit(file=img1)
        return content

    def testContentWithReferences(self):
        self.folder.invokeFactory('FAQ', id='test_faq')
        image = self.createImage()
        image2 = self.createImage(id='image2')
        portal_repository = self.portal_repository
        faq = self.folder.test_faq
        self.setFAQ(faq, 'v1')
        portal_repository.save(faq, comment='save no links')
        faq.setLinks([image.UID()])
        portal_repository.save(faq, comment='save with link')
        faq.setLinks([image2.UID()])
        portal_repository.save(faq, comment='save with other link')
        bothLinks = [image2.UID(), image.UID()]
        bothLinks.sort()
        faq.setLinks(bothLinks)
        portal_repository.save(faq, comment='save with other link')
        self.assertEquals(2, len(faq.getRawLinks()))
#         print "Link stuff", faq.getLinks()
#         print "Raw Link stuff", faq.getRawLinks()

        expected = [ (0, []),
            (1, [image.UID()]),
            (2, [image2.UID()]),
            (3, bothLinks)
            ]

        for version, explinks in expected:
            portal_repository.revert(faq, version)

            # Reverting reverts back the references
            links = faq.getRawLinks()
            links.sort()

            folderLinks = [ ref.targetUID for ref in faq.at_references.objectValues()]
            folderLinks.sort()

#             print "folderlinks", folderLinks
#             print "Link stuff", faq.getLinks()
#             print "Raw Link stuff", faq.getRawLinks()

            # XXX This assertion checks that the reference engine has
            # not been corrupted, but currently it fails.
            # XXX
            self.assertEquals(folderLinks, links,
                 "Version %d: links on object do not match reference catalog\nfolder %r, links %r" % (version, explinks, links))

            explinks.sort()
            self.assertEquals(explinks, folderLinks,
                "Version %d, expected %r, actual %r" % (version, explinks, folderLinks))

if HAS_AT:
    def test_suite():
        from unittest import TestSuite, makeSuite
        suite = TestSuite()
        suite.addTest(makeSuite(TestATContents))
        return suite
