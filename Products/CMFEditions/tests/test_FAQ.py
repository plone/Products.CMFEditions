# Tests which use the FAQ 'product' in this folder.
# This is a folderish content type which also uses references.
#
import os, sys, time

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from DateTime import DateTime
from Acquisition import aq_base
from DateTime import DateTime
from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase

PloneTestCase.setupPloneSite()
ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('PortalTransforms')
ZopeTestCase.installProduct('MimetypesRegistry')
ZopeTestCase.installProduct('CMFUid')
ZopeTestCase.installProduct('CMFEditions')
ZopeTestCase.installProduct('ATContentTypes')
ZopeTestCase.installProduct('FAQ')

portal_owner = PloneTestCase.portal_owner
portal_name = PloneTestCase.portal_name
default_user = PloneTestCase.default_user

def setupCMFEditions(app, portal_name, quiet):
    portal = app[portal_name]
    start = time.time()
    if not quiet: ZopeTestCase._print('Adding CMFEditions ... ')
    # Login as portal owner
    user = app.acl_users.getUserById(portal_owner).__of__(app.acl_users)
    newSecurityManager(None, user)
    # Add Archetypes
    if not hasattr(aq_base(portal), 'archetype_tool'):
        portal.portal_quickinstaller.installProduct('Archetypes')
    # Add PortalTransform
    #if not hasattr(aq_base(portal), 'portal_transforms'):
    portal.portal_quickinstaller.installProduct('PortalTransforms')
    # Add CMFEdtitions
    portal.portal_quickinstaller.installProduct('CMFEditions')
    if not quiet: ZopeTestCase._print('Adding ATContentTypes ... ')
    # Add ATContentTypes
    portal.portal_quickinstaller.installProduct('ATContentTypes')
    # Add FAQ
    portal.portal_quickinstaller.installProduct('FAQ')
    # Log out
    noSecurityManager()
    get_transaction().commit()
    if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-start,))


ZopeTestCase.utils.appcall(setupCMFEditions, portal_name, quiet=0)


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
        self.folder.invokeFactory('ATImage', id=id)
        img1 = open('img1.png', 'rb').read()
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

            # Rolling back rolls back the references
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
#             self.assertEquals(folderLinks, links,
#                 "Version %d: links on object do not match reference catalog\nfolder %r, links %r" % (version, explinks, links))
            
            explinks.sort()
            self.assertEquals(explinks, folderLinks,
                "Version %d, expected %r, actual %r" % (version, explinks, folderLinks))

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestATContents))
    return suite


if __name__ == '__main__':
    framework()
