# -*- coding: utf-8 -*-
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
"""Test the standard archivist

"""

from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase

import transaction
from zope.interface.verify import verifyObject
from Products.CMFCore.utils import getToolByName

from Products.CMFEditions.interfaces.IRepository import ICopyModifyMergeRepository
from Products.CMFEditions.interfaces.IRepository import IPurgeSupport
from Products.CMFEditions.interfaces.IRepository import RepositoryPurgeError
from Products.CMFEditions.interfaces.IRepository import IContentTypeVersionPolicySupport
from Products.CMFEditions.interfaces.IRepository import IVersionData
from Products.CMFEditions.VersionPolicies import VersionPolicy
from Products.CMFEditions.VersionPolicies import ATVersionOnEditPolicy

from DummyTools import DummyArchivist
from DummyTools import notifyModified

class dummyPolicyWithHooks(VersionPolicy):
    """A dummy policy to test the hooks"""
    def setupPolicyHook(self, portal, out):
        out.append('added')

    def removePolicyHook(self, portal, out):
        out.append('removed')

    def enablePolicyOnTypeHook(self, portal, p_type, out):
        out.append('enabled %s'%p_type)

    def disablePolicyOnTypeHook(self, portal, p_type, out):
        out.append('disabled %s'%p_type)

class TestCopyModifyMergeRepositoryToolBase(CMFEditionsBaseTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])

        # add an additional user
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')

        # add test data
        self.portal.invokeFactory('Document', 'doc')
        self.portal.invokeFactory('Link', 'link')
        self.portal.invokeFactory('Folder', 'fol')
        self.portal.fol.invokeFactory('Document', 'doc1_inside')
        self.portal.fol.invokeFactory('Document', 'doc2_inside')
        self.portal.fol.invokeFactory('Document', 'doc3_outside')

        self._setupArchivist()

    def _setupArchivist(self):
        # override this to install a different than the "official" tools
        pass

class TestCopyModifyMergeRepositoryTool(TestCopyModifyMergeRepositoryToolBase):

    def test00_interface(self):
        portal_repository = self.portal.portal_repository
        doc = self.portal.doc

        # test the tools interface conformance
        verifyObject(ICopyModifyMergeRepository, portal_repository)
        verifyObject(IPurgeSupport, portal_repository)

        # test the version data interface conformance
        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')

        vdata = portal_repository.retrieve(doc)
        verifyObject(IVersionData, vdata)

    def test01_saveVersionableAspects(self):
        portal_repository = self.portal.portal_repository
        portal_archivist = self.portal.portal_archivist
        doc = self.portal.doc

        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        doc.text = 'text v2'

        portal_repository.save(doc, comment='save no 2')

        vdata = portal_archivist.retrieve(obj=doc, selector=0)

        self.assertEqual(vdata.data.object.text, 'text v1')
        vdata = portal_archivist.retrieve(obj=doc, selector=1)
        self.assertEqual(vdata.data.object.text, 'text v2')

    def test02_retrieve(self):
        portal_repository = self.portal.portal_repository
        doc = self.portal.doc

        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        doc.text = 'text v2'
        portal_repository.save(doc, comment='save no 2')

        vdata = portal_repository.retrieve(doc, selector=0)
        self.failUnless(verifyObject(IVersionData, vdata))
        self.assertEqual(vdata.object.text, 'text v1')
        vdata = portal_repository.retrieve(doc, selector=1)
        self.assertEqual(vdata.object.text, 'text v2')

    def test03_recursiveRevertOfFolderWithOutsideObject(self):
        portal_repository = self.portal.portal_repository
        fol = self.portal.fol
        doc3_outside = fol.doc3_outside

        fol.title = 'fol title v1'
        doc3_outside.title = 'doc3_outside title text v1'
        portal_repository.applyVersionControl(fol, comment='save no 1')

        fol.title = 'fol title v2'
        doc3_outside.title = 'doc3_outside title text v2'
        portal_repository.save(fol, comment='save no 2')

        portal_repository.revert(fol, 0)

        # check result
        self.assertEqual(self.portal.fol, fol)
        self.assertEqual(self.portal.fol.doc3_outside, doc3_outside)

        self.assertEqual(fol.title, 'fol title v1')
        self.assertEqual(doc3_outside.title,
                        'doc3_outside title text v2')

    def test04_isUptoDate(self):
        portal_repository = self.portal.portal_repository
        doc = self.portal.doc

        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        self.assertEqual(portal_repository.isUpToDate(doc), True)
        doc.text = 'text v2'
        notifyModified(doc)
        self.failIf(portal_repository.isUpToDate(doc))

    def test05_getHistory(self):
        portal_repository = self.portal.portal_repository
        doc = self.portal.doc

        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        hist = portal_repository.getHistory(doc)
        self.assertEqual(hist._obj.text, 'text v1')
        self.assertEqual(len(hist), 1)

        doc.text = 'text v2'
        portal_repository.save(doc, comment='save no 2')
        hist = portal_repository.getHistory(doc)
        self.assertEqual(hist._obj.text, 'text v2')
        self.assertEqual(len(hist), 2)

    def test06_retrieveWithNoMoreExistentObject(self):
        portal_repository = self.portal.portal_repository
        portal_hidhandler = self.portal.portal_historyidhandler
        doc = self.portal.doc

        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        doc.text = 'text v2'
        portal_repository.save(doc, comment='save no 2')

        # save the ``history_id`` to be able to retrieve the object after
        # it's deletion
        history_id = portal_hidhandler.queryUid(doc)

        # delete the object we want to retrieve later
        doc_type = doc.getPortalTypeName()
        self.portal.manage_delObjects(ids=['doc'])
        self.portal.invokeFactory(doc_type, 'doc_tmp')
        doc = self.portal.doc_tmp
        portal_hidhandler.setUid(doc, history_id, check_uniqueness=True)
        vdata = portal_repository.retrieve(doc, selector=0)
        self.failUnless(verifyObject(IVersionData, vdata))
        self.assertEqual(vdata.object.text, 'text v1')
        vdata = portal_repository.retrieve(doc, selector=1)
        self.assertEqual(vdata.object.text, 'text v2')

    def test07_restoreDeletedObject(self):
        portal_repository = self.portal.portal_repository
        portal_hidhandler = self.portal.portal_historyidhandler
        doc = self.portal.doc

        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')

        # save the ``history_id`` to be able to retrieve the object after
        # it's deletion
        history_id = portal_hidhandler.queryUid(doc)

        # delete the object we want to retrieve later
        self.portal.manage_delObjects(ids=['doc'])
        self.failIf('doc' in self.portal.objectIds())
        portal_repository.restore(history_id, selector=0, container=self.portal)
        self.failUnless('doc' in self.portal.objectIds())
        restored = self.portal.doc
        self.assertEqual(restored.text, 'text v1')

    def test07_restoreDeletedObjectWithNewId(self):
        portal_repository = self.portal.portal_repository
        portal_hidhandler = self.portal.portal_historyidhandler
        doc = self.portal.doc

        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')

        # save the ``history_id`` to be able to retrieve the object after
        # it's deletion
        history_id = portal_hidhandler.queryUid(doc)

        # delete the object we want to retrieve later
        self.portal.manage_delObjects(ids=['doc'])
        self.failIf('doc' in self.portal.objectIds())
        portal_repository.restore(history_id, selector=0,
                                         container=self.portal, new_id='doc2')
        self.failUnless('doc2' in self.portal.objectIds())
        restored = self.portal.doc2
        self.assertEqual(restored.text, 'text v1')

    def test08_purgingDisallowedWithoutPurgingPolicy(self):
        portal_repository = self.portal.portal_repository
        doc = self.portal.doc

        # remove purge policy for this test
        portal_purgepolicy = self.portal.portal_purgepolicy
        del self.portal.portal_purgepolicy

        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')

        self.assertRaises(RepositoryPurgeError,
                          portal_repository.purge, doc, selector=0)

        self.portal.portal_purgepolicy = portal_purgepolicy

    def test09_getHistoryMetadata(self):
        portal_repository = self.portal.portal_repository
        doc = self.portal.doc
        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save number 1')
        doc.text = 'text v2'
        portal_repository.save(doc, comment='save number 2')

        history = portal_repository.getHistoryMetadata(doc)

        self.assertEqual(len(history), 2)
        # The history is acquisition wrapped
        self.assertEqual(history.aq_parent, doc)
        # check if timestamp and principal available
        self.failUnless(history.retrieve(1)['metadata']['sys_metadata']['timestamp'])
        self.failUnless(history.retrieve(0)['metadata']['sys_metadata']['principal'])
        # check if correct data and metadata retrieved
        self.assertEqual(history.retrieve(0)['metadata']['sys_metadata']['comment'], 'save number 1')
        self.assertEqual(history.retrieve(1)['metadata']['sys_metadata']['comment'], 'save number 2')



class TestRepositoryWithDummyArchivist(TestCopyModifyMergeRepositoryToolBase):

    def _setupArchivist(self):
        # replace the "original" tools by dummy tools
        tools = (
            DummyArchivist(),
        )
        for tool in tools:
            setattr(self.portal, tool.getId(), tool)

    def test01_recursiveSave(self):
        portal_repository = self.portal.portal_repository
        portal_repository.autoapply = False
        portal_archivist = self.portal.portal_archivist
        fol = self.portal.fol

        portal_archivist.reset_log()
        portal_repository.applyVersionControl(fol, comment='save no 1')
        portal_repository.save(fol, comment='save no 2')

        # check if correctly recursing and setting reference data correctly
        alog_str = portal_archivist.get_log()
        expected = """
prepare fol: hid=%(fol_id)s, refs=(doc1_inside, doc2_inside, doc3_outside)
  prepare doc1_inside: hid=%(doc1_id)s
  save    doc1_inside: hid=%(doc1_id)s, isreg=False, auto=True
  prepare doc2_inside: hid=%(doc2_id)s
  save    doc2_inside: hid=%(doc2_id)s, isreg=False, auto=True
save    fol: hid=%(fol_id)s, irefs=({hid:%(doc1_id)s, vid:0}, {hid:%(doc2_id)s, vid:0}), orefs=({hid:None, vid:-1}), isreg=False, auto=True

prepare fol: hid=%(fol_id)s, refs=(doc1_inside, doc2_inside, doc3_outside)
  prepare doc1_inside: hid=%(doc1_id)s
  save    doc1_inside: hid=%(doc1_id)s, isreg=True, auto=False
  prepare doc2_inside: hid=%(doc2_id)s
  save    doc2_inside: hid=%(doc2_id)s, isreg=True, auto=False
save    fol: hid=%(fol_id)s, irefs=({hid:%(doc1_id)s, vid:1}, {hid:%(doc2_id)s, vid:1}), orefs=({hid:None, vid:-1}), isreg=True, auto=False"""%{
            'fol_id': fol.cmf_uid(),
            'doc1_id': fol.doc1_inside.cmf_uid(),
            'doc2_id': fol.doc2_inside.cmf_uid()
            }

        self.assertEqual(alog_str, expected)

    def test02_recursiveRetrieve(self):
        portal_repository = self.portal.portal_repository
        portal_archivist = self.portal.portal_archivist
        fol = self.portal.fol

        fol.title = 'fol title v1'
        fol.doc1_inside.title = 'doc1_inside title text v1'
        fol.doc2_inside.title = 'doc2_inside title text v1'
        fol.doc3_outside.title = 'doc3_outside title text v1'
        portal_repository.applyVersionControl(fol, comment='save no 1')

        fol.title = 'fol title v2'
        fol.doc1_inside.title = 'doc1_inside title text v2'
        fol.doc2_inside.title = 'doc2_inside title text v2'
        fol.doc3_outside.title = 'doc3_outside title text v2'
        portal_repository.save(fol, comment='save no 2')

        portal_archivist.reset_log()

        retr = portal_repository.retrieve(fol, selector=0)

        # check recursive retrieve
        alog_str = portal_archivist.get_log()

        expected = """retrieve fol: hid=%(fol_id)s, selector=0
retrieve doc1_inside: hid=%(doc1_id)s, selector=0
retrieve doc2_inside: hid=%(doc2_id)s, selector=0"""%{
            'fol_id': fol.cmf_uid(),
            'doc1_id': fol.doc1_inside.cmf_uid(),
            'doc2_id': fol.doc2_inside.cmf_uid()
            }
        self.assertEqual(alog_str, expected)

        # check result
        self.assertEqual(retr.object.title, 'fol title v1')
        self.assertEqual(retr.object.doc1_inside.title,
                        'doc1_inside title text v1')
        self.assertEqual(retr.object.doc2_inside.title,
                        'doc2_inside title text v1')
        self.assertEqual(retr.object.doc3_outside.title,
                        'doc3_outside title text v2')


class TestRegressionTests(CMFEditionsBaseTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')

        self.portal.invokeFactory('Document', 'doc')
        self.portal.invokeFactory('Folder', 'fol')

        # add the Editions Tool (this way we test the 'Install' script!)
        self._setupArchivist()

    def _setupArchivist(self):
        # override this to install a different than the "official" tools
        pass

    def test_idModification(self):
        portal_repository = self.portal.portal_repository
        doc = self.portal.doc
        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        doc.text = 'text v2'
        transaction.savepoint(optimistic=True)
        self.portal.manage_renameObject(doc.getId(), 'newdoc',)
        portal_repository.save(doc, comment='save no 2')
        portal_repository.revert(doc, 0)
        self.assertEqual(doc.getId(), 'newdoc')
        self.failUnless('newdoc' in self.portal.objectIds())

class TestPolicyVersioning(TestCopyModifyMergeRepositoryToolBase):

    def afterSetUp(self):
        # define number of default policies
        TestCopyModifyMergeRepositoryToolBase.afterSetUp(self)
        self.np = len(self.portal.portal_repository.listPolicies())

    def isFCActionInPlace(self, object_id, status, button, context):
        fc = getToolByName(self.portal, 'portal_form_controller')
        for action in fc.listFormActions(1):
            if (object_id == action.getObjectId() and
                status == action.getStatus() and
                button == action.getButton() and
                context == action.getContextType()):
                return True
        return False

    def test00_interface(self):
        portal_repository = self.portal.portal_repository
        # test the tools interface conformance
        verifyObject(IContentTypeVersionPolicySupport, portal_repository)

    def test01_remove_policy_from_type(self):
        # test that policies can be removed
        portal_repository = self.portal.portal_repository
        # Set it twice to ensure that duplicates aren't created
        self.failUnless(portal_repository.supportsPolicy(self.portal.doc,
                                                        'at_edit_autoversion'))
        portal_repository.removePolicyFromContentType('Document',
                                                        'at_edit_autoversion')
        self.failIf(portal_repository.supportsPolicy(self.portal.doc,
                                                        'at_edit_autoversion'))

    def test02_set_policy_on_type(self):
        # test that policies can be set and retrieved
        portal_repository = self.portal.portal_repository
        self.failUnless(portal_repository.supportsPolicy(self.portal.doc,
                                                        'at_edit_autoversion'))
        portal_repository.removePolicyFromContentType('Document',
                                                        'at_edit_autoversion')
        self.failIf(portal_repository.supportsPolicy(self.portal.doc,
                                                        'at_edit_autoversion'))
        portal_repository.addPolicyForContentType('Document',
                                                        'at_edit_autoversion')
        self.failUnless(portal_repository.supportsPolicy(self.portal.doc,
                                                        'at_edit_autoversion'))

    def test03_set_policy_types_map(self):
        # test the mapping of policies to types
        portal_repository = self.portal.portal_repository
        # Get something in place first
        portal_repository.addPolicyForContentType('Document',
                                                        'at_edit_autoversion')
        portal_repository.removePolicyFromContentType('Document',
                                                        'at_edit_autoversion')
        # update the mapping
        portal_repository.manage_setTypePolicies({'Document':
                                                     ['at_edit_autoversion']})
        self.failUnless(portal_repository.supportsPolicy(self.portal.doc,
                                                       'at_edit_autoversion'))

        # assign two policies and then unassign them.
        # this demonstrates a bug related to modifying the list of policies
        # of a type while iterating through it.
        portal_repository.addPolicy('version_on_publish',
                                            'Create version when published')
        portal_repository.manage_setTypePolicies({'Document': [
                                                    'at_edit_autoversion',
                                                    'version_on_publish']})
        portal_repository.manage_setTypePolicies({'Document': []})
        self.failIf(portal_repository.supportsPolicy(self.portal.doc,
                                                       'at_edit_autoversion'))
        self.failIf(portal_repository.supportsPolicy(self.portal.doc,
                                                       'version_on_publish'))


    def test04_add_policy(self):
        # test adding a new policy
        portal_repository = self.portal.portal_repository
        self.assertEqual(len(portal_repository.listPolicies()), self.np)
        portal_repository.addPolicy('version_on_publish',
                                            'Create version when published')
        policies = portal_repository.listPolicies()
        self.assertEqual(len(policies), self.np+1)
        self.failUnless('version_on_publish' in [p.getId() for p in policies])

    def test04_add_policy_updates(self):
        # test calling addPolicy with an existing Id updates the title
        portal_repository = self.portal.portal_repository
        self.assertEqual(len(portal_repository.listPolicies()), self.np)
        portal_repository.addPolicy('at_edit_autoversion',
                                            'Fake policy title')
        policies = portal_repository.listPolicies()
        self.assertEqual(len(policies), self.np)
        self.failUnless('Fake policy title' in [p.Title() for p in policies])

    def test05_remove_policy(self):
        # test removing a policy removes the policy from all content types
        portal_repository = self.portal.portal_repository
        portal_repository.addPolicy('version_on_publish',
                                            'Create version when published')
        portal_repository.addPolicyForContentType('Document',
                                                        'version_on_publish')
        portal_repository.removePolicy('version_on_publish')
        self.assertEqual(len(portal_repository.listPolicies()), self.np)
        self.failIf(portal_repository.supportsPolicy(self.portal.doc,
                                                        'version_on_publish'))

    def test07_set_policy_defs(self):
        # test update policy definition list
        portal_repository = self.portal.portal_repository
        portal_repository.removePolicy('at_edit_autoversion')
        self.assertEqual(len(portal_repository.listPolicies()), self.np-1)
        portal_repository.manage_changePolicyDefs((('at_edit_autoversion',
                                            'Fake policy title'),))
        policies = portal_repository.listPolicies()
        self.assertEqual(len(policies), 1)
        self.failUnless('Fake policy title' in [p.Title() for p in policies])

    def test08_mutators_fail_on_invalid_input(self):
        portal_repository = self.portal.portal_repository
        # manage_changePolicyDefs requires a sequence of two-tuples with
        # strings
        self.assertRaises(AssertionError,
                            portal_repository.manage_changePolicyDefs,
                            {'at_edit_autoversion':'Fake policy title'})
        self.assertRaises(AssertionError,
                            portal_repository.manage_changePolicyDefs,
                            ('at_edit_autoversion','policy2'))
        self.assertRaises(AssertionError,
                            portal_repository.manage_changePolicyDefs,
                            [(1,'My new policy')])
        self.assertRaises(TypeError,
                            portal_repository.manage_changePolicyDefs,
                [('at_edit_autoversion','My new policy', 'some_extra_stuff')])
        self.assertRaises(AssertionError,
                            portal_repository.manage_changePolicyDefs,
        [('at_edit_autoversion','My new policy', dummyPolicyWithHooks,'str')])
        # manage_setTypePolicies requires a mapping of of portal_types to a
        # list of valid policies
        self.assertRaises(AssertionError,
                            portal_repository.manage_setTypePolicies,
                            {'my_type':'at_edit_autoversion'})
        self.assertRaises(AssertionError,
                            portal_repository.manage_setTypePolicies,
                            {'my_type':['a_bogus_policy']})
        self.assertRaises(AssertionError,
                            portal_repository.manage_setTypePolicies,
                            (('my_type',['a_bogus_policy']),))
        # addPolicyForContentType fails unless the policy is valid
        self.assertRaises(AssertionError,
                            portal_repository.addPolicyForContentType,
                            'my_type','my_bogus_policy')

    def test09_policy_hooks(self):
        portal_repository = self.portal.portal_repository
        out = []
        # Test hooks on basic actions
        portal_repository.addPolicy('my_bogus_policy',
                                  'Hook Tests', dummyPolicyWithHooks, out=out)
        self.assertEqual(out, ['added'])
        self.assertEqual(len(portal_repository.listPolicies()), self.np+1)
        portal_repository.addPolicyForContentType('Document',
                                                   'my_bogus_policy', out=out)
        self.failUnless(portal_repository.supportsPolicy(self.portal.doc,
                                                        'my_bogus_policy'))
        self.assertEqual(out, ['added','enabled Document'])
        portal_repository.removePolicyFromContentType('Document',
                                                   'my_bogus_policy', out=out)
        self.failIf(portal_repository.supportsPolicy(self.portal.doc,
                                                        'my_bogus_policy'))
        self.assertEqual(out, ['added','enabled Document',
                                                    'disabled Document'])
        portal_repository.removePolicy('my_bogus_policy', out=out)
        self.assertEqual(out, ['added','enabled Document',
                                            'disabled Document','removed'])
        self.assertEqual(len(portal_repository.listPolicies()), self.np)

    def test10_remove_policy_disables_types_first(self):
        # Ensure that removal calls the type removal hooks
        portal_repository = self.portal.portal_repository
        out = []
        portal_repository.addPolicy('my_bogus_policy',
                                  'Hook Tests', dummyPolicyWithHooks, out=out)
        portal_repository.addPolicyForContentType('Document',
                                                   'my_bogus_policy', out=out)
        portal_repository.removePolicy('my_bogus_policy', out=out)
        self.assertEqual(out, ['added','enabled Document',
                                            'disabled Document','removed'])

    def test11_set_policy_calls_all_hooks(self):
        # Explicitly setting policies removes/disables all old policies and
        # adds/enables new ones.
        portal_repository = self.portal.portal_repository
        out = []
        portal_repository.addPolicy('my_bogus_policy',
                                  'Hook Tests', dummyPolicyWithHooks, out=out)
        portal_repository.addPolicyForContentType('Document',
                                                   'my_bogus_policy', out=out)
        portal_repository.manage_changePolicyDefs((('my_bogus_policy2',
                  'Fake title', dummyPolicyWithHooks, {'out':out}),), out=out)
        self.assertEqual(out, ['added','enabled Document','disabled Document',
                    'removed','added'])

    def test12_set_policy_types_map_calls_all_hooks(self):
        # Explicitly setting policies removes/disables all old policies and
        # adds/enables new ones.
        portal_repository = self.portal.portal_repository
        out = []
        portal_repository.addPolicy('my_bogus_policy',
                                  'Hook Tests', dummyPolicyWithHooks, out=out)
        portal_repository.addPolicyForContentType('Document',
                                                   'my_bogus_policy', out=out)
        portal_repository.manage_setTypePolicies({'Event':
                                                         ['my_bogus_policy']},
                                                         out=out)
        self.assertEqual(out, ['added','enabled Document','disabled Document',
                    'enabled Event'])

    def test13_at_auto_version_hooks(self):
        portal_repository = self.portal.portal_repository
        # Check if the form controller hook is in place:
        self.failUnless(self.isFCActionInPlace('validate_integrity',
                                                     'success', None, None))
        self.failUnless(self.isFCActionInPlace('atct_edit',
                                                     'success', None, None))
        # Remove policy and check if hook is removed
        portal_repository.removePolicy('at_edit_autoversion')
        self.failIf(self.isFCActionInPlace('validate_integrity',
                                                 'success', None, None))
        self.failIf(self.isFCActionInPlace('atct_edit',
                                                     'success', None, None))
        # Add policy and check if hook is added
        portal_repository.addPolicy('at_edit_autoversion', 'Auto policy',
                                     ATVersionOnEditPolicy)
        self.failUnless(self.isFCActionInPlace('validate_integrity',
                                                     'success', None, None))
        self.failUnless(self.isFCActionInPlace('atct_edit',
                                                     'success', None, None))

    def test14_has_policy(self):
        portal_repository = self.portal.portal_repository
        # We already have two policies by default
        self.failUnless(portal_repository.hasPolicy(self.portal.doc))
        portal_repository.removePolicyFromContentType('Document',
                                                        'at_edit_autoversion')
        portal_repository.removePolicyFromContentType('Document',
                                                        'version_on_revert')
        self.failIf(portal_repository.hasPolicy(self.portal.doc))
