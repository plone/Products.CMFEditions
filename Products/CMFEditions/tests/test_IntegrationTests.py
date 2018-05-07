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
"""Top level integration tests (without UI)

"""
from Acquisition import aq_base
from plone.app.textfield.value import RichTextValue
from Products.CMFCore.indexing import processQueue
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase
from ZODB import broken
from zope.component.persistentregistry import PersistentComponents
from zope.interface.interface import InterfaceClass

import ZODB.interfaces
import imp
import sys
import transaction

try:
    from AccessControl.rolemanager import _string_hash
    has_zope4 = True
except ImportError:
    has_zope4 = False


class TestIntegration(CMFEditionsBaseTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager', ])

        # add an additional user
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')
        # add a document
        self.portal.invokeFactory('Document', 'doc')

        # add a folder with two documents in it
        self.portal.invokeFactory('Folder', 'fol')
        self.portal.fol.invokeFactory('Document', 'doc1')
        self.portal.fol.invokeFactory('Document', 'doc2')

    def test01_assertApplyVersionControlSavesOnlyOnce(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        doc.setTitle('doc title v1')
        portal_repo.applyVersionControl(doc, comment='First version')

        # there should be only one history entry and not two or more
        self.assertEqual(len(portal_repo.getHistory(doc)), 1)

    def test02_storeAndRevertToPreviousVersion(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        doc.setTitle("v1")
        portal_repo.applyVersionControl(doc)
        doc.setTitle("v2")
        portal_repo.save(doc)
        doc.setTitle("v3")

        self.assertEqual(doc.Title(), "v3")

        portal_repo.revert(doc)
        # just a remark: we don't do "doc = self.portal.doc" to check for
        # inplace replacement
        self.assertEqual(doc.Title(), "v2")

    def test03_revertToSpecificVersion(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        # store the work edition two times
        doc.setTitle("v1")
        portal_repo.applyVersionControl(doc)
        doc.setTitle("v2")
        portal_repo.save(doc)
        doc.setTitle("v3")
        portal_repo.save(doc)
        doc.setTitle("v4")
        self.assertEqual(doc.Title(), "v4")

        # revert to the the last but one version
        portal_repo.revert(doc, 1)
        self.assertEqual(doc.Title(), "v2")

    def test04_storeAndRevertToPreviousVersionAndStoreAgain(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        doc.setTitle("v1")
        portal_repo.applyVersionControl(doc)
        doc.setTitle("v2")
        portal_repo.save(doc)
        doc.setTitle("v3")
        self.assertEqual(doc.Title(), "v3")

        portal_repo.revert(doc, 0)
        doc = self.portal.doc
        self.assertEqual(doc.Title(), "v1")
        doc.setTitle("v4")
        portal_repo.save(doc)
        self.assertEqual(doc.Title(), "v4")

    def test05_getHistory(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        # store and publish certain times
        portal_repo.applyVersionControl(doc)

        portal_repo.save(doc, metadata="v2\nsecond line")
        portal_repo.save(doc)

        history = portal_repo.getHistory(doc)

        # test the number of history entries
        self.assertEqual(len(history), 3)

        """XXX we like to test that but implementation isn't there yet
        # test some of the log entries"""
        h1 = history[1]
        self.assertEqual(h1.version_id, 1)
        # self.assertEqual(h1.action, h1.ACTION_CHECKIN)
        # self.assertEqual(h1.message, 'v2\nsecond line')
        # self.assertTrue(h1.user_id)
        # self.assertEqual(h1.path, '/'.join(doc.getPhysicalPath()))
        # self.assertTrue(h1.timestamp)

    def test06_retrieveSpecificVersion(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        review_state = self.portal.portal_workflow.getInfoFor(
            doc, 'review_state')

        # store the work edition two times
        doc.setTitle("v1")
        portal_repo.applyVersionControl(doc)
        doc.setTitle("v2")
        portal_repo.save(doc)
        doc.setTitle("v3")
        portal_repo.save(doc)
        doc.setTitle("v4")
        self.assertEqual(doc.Title(), "v4")

        retrieved_doc = portal_repo.retrieve(doc, 1)

        self.assertEqual(retrieved_doc.object.Title(), "v2")
        self.assertEqual(doc.Title(), "v4")
        self.assertEqual(self.portal.doc.Title(), "v4")

        # since 1.0beta1 the workflows review state is saved to the
        # system metadata by a modifier.
        self.assertEqual(
            retrieved_doc.sys_metadata["review_state"], review_state)

    def test07_cloneObjectUnderVersionControlRemovesOriginalsHistory(self):
        portal_repo = self.portal.portal_repository
        portal_historyidhandler = self.portal.portal_historyidhandler
        doc = self.portal.doc

        # put the object under version control
        portal_repo.applyVersionControl(doc)

        # copy
        self.portal.manage_pasteObjects(
            self.portal.manage_copyObjects(ids=['doc']))
        copy = self.portal.copy_of_doc

        # the copy shall not have a history yet: that's correct
        self.assertFalse(portal_repo.getHistory(copy))

        # just to be sure the history is definitivels different
        self.assertNotEqual(
            portal_historyidhandler.queryUid(doc),
            portal_historyidhandler.queryUid(copy))  # may be None

    def test08_loopOverHistory(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        # put the object under version control
        portal_repo.applyVersionControl(doc)

        counter = 0
        for v in portal_repo.getHistory(doc):
            counter += 1

        # check if history iterator returned just one element
        self.assertEquals(counter, 1)

    def test09_retrieveAndRevertRetainWorkingCopiesWorkflowInfo(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        doc.review_state = "fake rev state v1"
        doc.workflow_history = {0: "fake wf history v1"}

        portal_repo.applyVersionControl(doc)

        doc.review_state = "fake rev state v2"
        doc.workflow_history = {0: "fake wf history v2"}
        portal_repo.save(doc)

        # just check the original is unchanged
        self.assertEqual(doc.review_state, "fake rev state v2")
        self.assertEqual(doc.workflow_history[0], "fake wf history v2")

        # ----- retrieve
        # check if retrieved object carries the working copies workflow info
        retrieved_data = portal_repo.retrieve(
            doc, 0, preserve=['review_state', 'workflow_history'])
        self.assertEqual(retrieved_data.object.review_state,
                         "fake rev state v2")
        self.assertEqual(retrieved_data.object.workflow_history[0],
                         "fake wf history v2")

        # check that the working copies workflow info is unchanged
        self.assertEqual(doc.review_state, "fake rev state v2")
        self.assertEqual(doc.workflow_history[0], "fake wf history v2")

        # check if the preserved data is returned correctly
        preserved_rvs = retrieved_data.preserved_data['review_state']
        self.assertEqual(preserved_rvs, "fake rev state v1")
        preserved_wfh = retrieved_data.preserved_data['workflow_history'][0]
        self.assertEqual(preserved_wfh, "fake wf history v1")

        # ----- revert
        # check that the working copies workflow info is unchanged after
        portal_repo.revert(doc, 0)
        self.assertEqual(doc.review_state, "fake rev state v2")
        self.assertEqual(doc.workflow_history[0], "fake wf history v2")

    def test10_versionAStandardFolder(self):
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")
        doc2.setTitle("v1 of doc2")

        portal_repo.applyVersionControl(fol, comment='first save')

        # save change no 2
        fol.setTitle('v2 of fol')
        doc1.setTitle("v2 of doc1")
        doc2.setTitle("v2 of doc2")
        portal_repo.save(fol, comment='second save')

        # change no 3 (without saving)
        fol.setTitle('v3 of fol')
        doc1.setTitle("v3 of doc1")
        doc2.setTitle("v3 of doc2")

        # revert to change no 2
        portal_repo.revert(fol)

        # check if revertion worked correctly
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2
        self.assertEqual(fol.Title(), "v2 of fol")
        self.assertEqual(doc1.Title(), "v3 of doc1")
        self.assertEqual(doc2.Title(), "v3 of doc2")

    def test11_versionAFolderishObjectThatTreatsChildrensAsInsideRefs(self):
        portal_repo = self.portal.portal_repository
        portal_historyidhandler = self.portal.portal_historyidhandler
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2

        # just configure the standard folder to treat the childrens as
        # inside refrences. For this we reconfigure the standard modifiers.
        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")
        doc2.setTitle("v1 of doc2")
        portal_repo.applyVersionControl(fol, comment='first save')
        orig_uid1 = portal_historyidhandler.queryUid(doc1)
        orig_uid2 = portal_historyidhandler.queryUid(doc2)

        # save change no 2
        fol.setTitle('v2 of fol')
        doc1.setTitle("v2 of doc1")
        doc2.setTitle("v2 of doc2")
        portal_repo.save(fol, comment='second save after we deleted doc2')

        # save change no 3
        fol.setTitle('v3 of fol')
        doc1.setTitle("v3 of doc1")
        fol.manage_delObjects(ids=['doc2'])
        fol.invokeFactory('Document', 'doc3')
        doc3 = fol.doc3
        doc3.setTitle("v1 of doc3")
        portal_repo.save(fol, comment='second save with new doc3')

        # revert to change no 1 (version idexes start with index 0)
        portal_repo.revert(fol, selector=1)

        # check if revertion worked correctly
        fol = self.portal.fol
        doc1 = fol.doc1
        self.assertTrue('doc2' in fol.objectIds())
        self.assertFalse('doc3' in fol.objectIds())
        doc2 = fol.doc2
        self.assertEqual(fol.Title(), "v2 of fol")
        self.assertEqual(doc1.Title(), "v2 of doc1")
        self.assertEqual(doc2.Title(), "v2 of doc2")
        self.assertEqual(portal_historyidhandler.queryUid(doc1), orig_uid1)
        self.assertEqual(portal_historyidhandler.queryUid(doc2), orig_uid2)

    def test12_retrieveAndRevertRetainWorkingCopiesPermissions(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc
        perm = 'Access contents information'
        if has_zope4:
            member_role = 'permission_{0}role_{1}'.format(
                _string_hash(perm),
                _string_hash('Member')
            )
        else:
            roles = list(doc.valid_roles())
            member_role = 'p0r{0}'.format(roles.index('Member'))

        doc.manage_permission(perm, ('Manager',), 0)

        portal_repo.applyVersionControl(doc)

        doc.manage_permission(perm, ('Manager', 'Member'), 1)
        portal_repo.save(doc)

        # just check the original is unchanged
        settings = doc.permission_settings(perm)[0]
        self.assertTrue(settings['acquire'])
        role_enabled = [r for r in settings['roles']
                        if r['name'] == member_role][0]
        self.assertTrue(role_enabled['checked'])

        # ----- retrieve
        # check if retrieved object carries the working copy's permissions
        retrieved_data = portal_repo.retrieve(
            doc, 0, preserve=['_Access_contents_information_Permission'])
        settings = retrieved_data.object.permission_settings(perm)[0]
        self.assertTrue(settings['acquire'])
        role_enabled = [
            r for r in settings['roles']
            if r['name'] == member_role
        ][0]
        self.assertTrue(role_enabled['checked'])

        # check that the working copy's permissions are unchanged
        settings = doc.permission_settings(perm)[0]
        self.assertTrue(settings['acquire'])
        role_enabled = [
            r for r in settings['roles']
            if r['name'] == member_role
        ][0]
        self.assertTrue(role_enabled['checked'])

        # check if the preserved data is returned correctly
        preserved = retrieved_data.preserved_data['_Access_contents_information_Permission']  # noqa
        self.assertEqual(preserved, ('Manager',))

        # ----- revert
        # check that the working copies permissions are unchanged after revert
        portal_repo.revert(doc, 0)
        settings = doc.permission_settings(perm)[0]
        self.assertTrue(settings['acquire'])
        role_enabled = [r for r in settings['roles']
                        if r['name'] == member_role][0]
        self.assertTrue(role_enabled['checked'])

    def test13_revertUpdatesCatalog(self):
        portal_repo = self.portal.portal_repository
        cat = self.portal.portal_catalog
        doc = self.portal.doc

        doc.text = RichTextValue(u'Plain text', 'text/plain', 'text/plain')
        portal_repo.applyVersionControl(doc)
        doc.text = RichTextValue(u'blahblah', 'text/plain', 'text/plain')
        portal_repo.save(doc)
        # Test that catalog has current value
        results = cat(SearchableText='Plain Text')
        self.assertEqual(len(results), 0)
        results = cat(SearchableText='blahblah')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject(), doc)

        retrieved_data = portal_repo.retrieve(
            doc, 0, preserve=['_Access_contents_information_Permission'])
        retrieved_doc = retrieved_data.object
        self.assertTrue('Plain text' in retrieved_doc.text.raw)
        # Test that basic retrieval did not alter the catalog
        results = cat(SearchableText='Plain Text')
        self.assertEqual(len(results), 0)
        results = cat(SearchableText='blahblah')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject(), doc)

        portal_repo.revert(doc, 0)
        # Test that the catalog is updated on revert
        results = cat(SearchableText='blahblah')
        self.assertEqual(len(results), 0)
        results = cat(SearchableText='Plain Text')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject().text.raw, 'Plain text')

    def test14_retrieveFolderWithAddedOrDeletedObjects(self):
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")
        doc2.setTitle("v1 of doc2")

        portal_repo.applyVersionControl(fol, comment='first save')

        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_folder = retrieved_data.object
        self.assertEqual(ret_folder.objectIds(), fol.objectIds())
        self.assertEqual(tuple(ret_folder.objectValues()),
                         tuple(fol.objectValues()))

        # remove an item
        fol.manage_delObjects('doc2')

        # retrieve should update sub-objects
        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_folder = retrieved_data.object
        self.assertEqual(ret_folder.objectIds(), fol.objectIds())
        self.assertEqual(tuple(ret_folder.objectValues()),
                         tuple(fol.objectValues()))

        # add it back
        fol.invokeFactory('Document', 'doc2')
        doc2 = fol.doc2
        doc2.setTitle('v2 of doc2')

        # retrieve should update sub-objects
        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_folder = retrieved_data.object
        self.assertEqual(ret_folder.objectIds(), fol.objectIds())
        self.assertEqual(tuple(ret_folder.objectValues()),
                         tuple(fol.objectValues()))
        self.assertEqual(ret_folder.doc2.Title(), 'v2 of doc2')

        # add new item
        fol.invokeFactory('Document', 'doc3')
        doc3 = fol.doc3
        doc3.setTitle('v1 of doc3')

        # retrieve should copy new sub-objects
        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_folder = retrieved_data.object
        self.assertEqual(ret_folder.objectIds(), fol.objectIds())
        self.assertEqual(tuple(ret_folder.objectValues()),
                         tuple(fol.objectValues()))
        self.assertEqual(ret_folder.doc3.Title(), 'v1 of doc3')

        orig_ids = fol.objectIds()
        orig_values = fol.objectValues()
        # revert to original state, ensure that subobject changes are
        # preserved
        portal_repo.revert(fol, 0)

        # check if reversion worked correctly
        self.assertEqual(tuple(fol.objectIds()), tuple(orig_ids))
        self.assertEqual(tuple(fol.objectValues()), tuple(orig_values))

        # XXX we should be preserving order as well

    def test15_retrieveInsideRefsFolderWithAddedOrDeletedObjects(self):
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2

        # just configure the standard folder to treat the children as
        # inside references. For this we reconfigure the standard modifiers.
        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")
        doc2.setTitle("v1 of doc2")

        orig_ids = fol.objectIds()
        orig_values = fol.objectValues()

        portal_repo.applyVersionControl(fol, comment='first save')

        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_folder = retrieved_data.object
        self.assertEqual(ret_folder.objectIds(), orig_ids)
        ret_values = ret_folder.objectValues()
        # The values are not identical to the stored values because they are
        # retrieved from the repository.
        for i in range(len(ret_values)):
            self.assertEqual(ret_values[i].getId(), orig_values[i].getId())
            self.assertEqual(ret_values[i].Title(), orig_values[i].Title())

        # remove an item
        fol.manage_delObjects('doc2')
        processQueue()

        cur_ids = fol.objectIds()
        self.assertEqual(len(cur_ids), 1)

        # retrieve should retrieve missing sub-objects
        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_folder = retrieved_data.object
        self.assertEqual(ret_folder.objectIds(), orig_ids)
        ret_values = ret_folder.objectValues()
        for i in range(len(ret_values)):
            self.assertEqual(ret_values[i].getId(), orig_values[i].getId())
            self.assertEqual(ret_values[i].Title(), orig_values[i].Title())
        # We should not have altered the folder itself on retrieve
        self.assertEqual(fol.objectIds(), cur_ids)

        # add new item
        fol.invokeFactory('Document', 'doc3')
        doc3 = fol.doc3
        doc3.setTitle('v1 of doc3')

        cur_ids = fol.objectIds()
        self.assertEqual(len(cur_ids), 2)

        # retrieve should not add new sub-objects
        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_folder = retrieved_data.object
        self.assertEqual(ret_folder.objectIds(), orig_ids)
        ret_values = ret_folder.objectValues()
        for i in range(len(ret_values)):
            self.assertEqual(ret_values[i].getId(), orig_values[i].getId())
            self.assertEqual(ret_values[i].Title(), orig_values[i].Title())
        # We should not have altered the folder itself on retrieve
        self.assertEqual(fol.objectIds(), cur_ids)

        # revert to original state, ensure that subobject changes are
        # reverted
        portal_repo.revert(fol, 0)
        fol = self.portal.fol

        # check if reversion worked correctly
        self.assertEqual(fol.objectIds(), orig_ids)
        for i in range(len(ret_values)):
            self.assertEqual(ret_values[i].getId(), orig_values[i].getId())
            self.assertEqual(ret_values[i].Title(), orig_values[i].Title())

    def test16_revertInsideRefsUpdatesCatalog(self):
        portal_repo = self.portal.portal_repository
        cat = self.portal.portal_catalog
        fol = self.portal.fol
        doc = fol.doc1

        # just configure the standard folder to treat the childrens as
        # inside refrences. For this we reconfigure the standard modifiers.
        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")

        # save change no 1
        fol.setTitle('v1 of fol')
        doc.setTitle("v1 of doc1")
        fol.reindexObject()
        doc.reindexObject()
        portal_repo.applyVersionControl(fol, comment='first save')

        # save change no 2
        fol.setTitle('v2 of fol')
        doc.setTitle("v2 of doc1")
        fol.reindexObject()
        doc.reindexObject()
        portal_repo.save(fol, comment='second save')

        # Test that catalog has current value
        results = cat(SearchableText='v1')
        self.assertEqual(len(results), 0)
        results = cat(SearchableText='v2', portal_type='Document')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject(), doc)

        retrieved_data = portal_repo.retrieve(
            fol, 0, preserve=['_Access_contents_information_Permission'])
        retrieved_doc = retrieved_data.object.doc1
        self.assertEqual(retrieved_doc.Title(), 'v1 of doc1')
        # Test that basic retrieval did not alter the catalog
        results = cat(SearchableText='v1', )
        self.assertEqual(len(results), 0)
        results = cat(SearchableText='v2', portal_type='Document')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject(), doc)

        portal_repo.revert(fol, 0)
        reverted_doc = self.portal.fol.doc1
        self.assertEqual(reverted_doc.Title(), 'v1 of doc1')
        # Test that the catalog is updated on revert
        results = cat(SearchableText='v2')
        self.assertEqual(len(results), 0)
        results = cat(SearchableText='v1', portal_type='Document')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject().Title(), 'v1 of doc1')

    def test17_moveInsideRefThenRevertChangesUid(self):
        # When an object is contained in an 'Inside references folder' and
        # has been moved into another location, it should maintain its CMF Uid,
        # if the folder is then reverted to a state where it contained the
        # object (which now exists with the same uid in a different location),
        # the uid of the reverted object should be changed.
        portal_repo = self.portal.portal_repository
        portal_historyidhandler = self.portal.portal_historyidhandler
        fol = self.portal.fol
        doc1 = fol.doc1

        # just configure the standard folder to treat the childrens as
        # inside refrences. For this we reconfigure the standard modifiers.
        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")

        portal_repo.applyVersionControl(fol, comment='first save')
        orig_uid = portal_historyidhandler.queryUid(doc1)

        transaction.savepoint(optimistic=True)
        self.portal.manage_pasteObjects(fol.manage_cutObjects(ids=['doc1']))
        moved_doc = self.portal.doc1
        self.assertEqual(portal_historyidhandler.queryUid(moved_doc), orig_uid)
        transaction.savepoint(optimistic=True)

        # retrieve should change the uid if it already exists
        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_folder = retrieved_data.object
        ret_doc = ret_folder.doc1
        self.assertFalse(portal_historyidhandler.queryUid(ret_doc) == orig_uid,
                    "UIDs should not be equal, current value: %s" % orig_uid)

        # revert to original state, ensure that subobject changes are
        # reverted and that uid is changed
        portal_repo.revert(fol, 0)
        fol = self.portal.fol
        reverted_doc = fol.doc1

        # check if reversion worked correctly
        self.assertFalse(portal_historyidhandler.queryUid(reverted_doc) == orig_uid,
                    "UIDs should not be equal, current value: %s" % orig_uid)

    def test18_retrieveObjectWhichHasBeenReplaced(self):
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")
        doc2.setTitle("v1 of doc2")

        portal_repo.applyVersionControl(doc1, comment='first save')
        portal_repo.applyVersionControl(doc2, comment='first save')

        transaction.savepoint(optimistic=True)
        fol.manage_renameObjects(['doc1', 'doc2'], ['doc1_renamed', 'doc1'])

        doc1 = fol.doc1_renamed
        doc2 = fol.doc1

        doc1.setTitle('v2 of doc1_renamed')
        doc2.setTitle('v2 of doc1 (was doc2)')

        portal_repo.save(doc1, comment='second save')
        portal_repo.save(doc2, comment='second save')

        retrieved_data = portal_repo.retrieve(doc1, 0)
        ret_doc = retrieved_data.object
        self.assertEqual(ret_doc.getId(), 'doc1')
        self.assertEqual(ret_doc.Title(), 'v1 of doc1')

        portal_repo.revert(doc1, 0)
        rev_doc = fol.doc1_renamed
        self.assertEqual(rev_doc.getId(), 'doc1_renamed')
        self.assertEqual(rev_doc.Title(), 'v1 of doc1')

    def disabled_test19_retrieveDeletedObjectWhichHasBeenReplacedInAnInsideRefsFolder(self):  # noqa
        # disabled by gregweb/21-10-2006
        # reason: Needs concentrated and deeper look.
        # --> Ideas exist, pleas contact us on the list if you like to work
        #     on that.
        # I know one should not do that! But solving this would bring more
        # risks into the 1.0final than leaving the bug to be solved afterwards.
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2

        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")
        doc2.setTitle("v1 of doc2")

        portal_repo.applyVersionControl(fol, comment='first save')

        fol.manage_delObjects(['doc1'])
        transaction.savepoint(optimistic=True)
        fol.manage_renameObjects(['doc2'], ['doc1'])

        doc2 = fol.doc1

        doc1.setTitle('v2 of doc1_renamed')
        doc2.setTitle('v2 of doc1 (was doc2)')

        portal_repo.save(fol, comment='second save')

        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_fol = retrieved_data.object
        self.assertEqual(ret_fol.objectIds(), ['doc1', 'doc2'])
        ret_doc1 = ret_fol.doc1
        ret_doc2 = ret_fol.doc2
        self.assertEqual(ret_doc1.getId(), 'doc1')
        self.assertEqual(ret_doc1.Title(), 'v1 of doc1')
        self.assertEqual(ret_doc2.getId(), 'doc2')
        self.assertEqual(ret_doc2.Title(), 'v1 of doc2')

        portal_repo.revert(fol, 0)
        rev_fol = self.portal.fol
        self.assertEqual(rev_fol.objectIds(), ['doc1', 'doc2'])
        rev_doc1 = rev_fol.doc1
        rev_doc2 = rev_fol.doc2
        self.assertEqual(rev_doc1.getId(), 'doc1')
        self.assertEqual(rev_doc1.Title(), 'v1 of doc1')
        self.assertEqual(rev_doc2.getId(), 'doc2')
        self.assertEqual(rev_doc2.Title(), 'v1 of doc2')

    def disabled_test20_retrieveMovedObjectWhichHasBeenReplacedInAnInsideRefsFolder(self):  # noqa
        # disabled by gregweb/21-10-2006
        # reason: Needs concentrated and deeper look.
        # --> Ideas exist, pleas contact us on the list if you like to work
        #     on that.
        # I know one should not do that! But solving this would bring more
        # risks into the 1.0final than leaving the bug to be solved afterwards.
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2

        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")
        doc2.setTitle("v1 of doc2")

        portal_repo.applyVersionControl(fol, comment='first save')

        transaction.savepoint(optimistic=True)
        self.portal.manage_pasteObjects(fol.manage_cutObjects(['doc1']))
        fol.manage_renameObjects(['doc2'], ['doc1'])

        doc2 = fol.doc1
        doc1 = self.portal.doc1

        doc1.setTitle('v2 of doc1 (now in portal root)')
        doc2.setTitle('v2 of doc1 (was doc2)')

        portal_repo.save(fol, comment='second save')

        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_fol = retrieved_data.object
        self.assertEqual(ret_fol.objectIds(), ['doc1', 'doc2'])
        ret_doc1 = ret_fol.doc1
        ret_doc2 = ret_fol.doc2
        self.assertEqual(ret_doc1.getId(), 'doc1')
        self.assertEqual(ret_doc1.Title(), 'v1 of doc1')
        self.assertEqual(ret_doc2.getId(), 'doc2')
        self.assertEqual(ret_doc2.Title(), 'v1 of doc2')

        retrieved_data = portal_repo.revert(fol, 0)
        rev_fol = self.portal.fol
        self.assertEqual(rev_fol.objectIds(), ['doc1', 'doc2'])
        rev_doc1 = rev_fol.doc1
        rev_doc2 = rev_fol.doc2
        self.assertEqual(rev_doc1.getId(), 'doc1')
        self.assertEqual(rev_doc1.Title(), 'v1 of doc1')
        self.assertEqual(rev_doc2.getId(), 'doc2')
        self.assertEqual(rev_doc2.Title(), 'v1 of doc2')

    def test21_DontLeaveDanglingCatalogEntriesWhenInvokingFactory(self):
        portal_repo = self.portal.portal_repository
        catalog = self.portal.portal_catalog
        fol = self.portal.fol
        doc1 = fol.doc1
        doc2 = fol.doc2

        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")

        # save change no 1
        fol.setTitle('v1 of fol')
        doc1.setTitle("v1 of doc1")
        doc2.setTitle("v1 of doc2")

        portal_repo.applyVersionControl(fol, comment='first save')

        self.assertEqual(len(catalog(getId='doc1')), 1)

        fol.manage_delObjects(['doc2', 'doc1'])

        self.assertEqual(len(catalog(getId='doc1')), 0)

        portal_repo.save(fol, comment='second save')

        retrieved_data = portal_repo.retrieve(fol, 0)
        ret_fol = retrieved_data.object
        self.assertEqual(ret_fol.objectIds(), ['doc1', 'doc2'])
        self.assertEqual(len(catalog(getId='doc1')), 0)

        portal_repo.revert(fol, 0)
        rev_fol = self.portal.fol
        self.assertEqual(rev_fol.objectIds(), ['doc1', 'doc2'])
        self.assertEqual(len(catalog(getId='doc1')), 1)

    def test21_RevertObjectWithChangedIdMaintainsConsistentCatalog(self):
        portal_repo = self.portal.portal_repository
        catalog = self.portal.portal_catalog
        fol = self.portal.fol
        doc1 = fol.doc1

        # save change no 1
        doc1.setTitle("v1 of doc1")

        portal_repo.applyVersionControl(doc1, comment='first save')

        self.assertEqual(len(catalog(getId='doc1')), 1)

        doc1.setTitle("v2 of doc1")
        transaction.savepoint()
        fol.manage_renameObject('doc1', 'doc1_changed')
        doc1 = fol.doc1_changed
        doc1.reindexObject()

        self.assertEqual(len(catalog(getId='doc1')), 0)
        self.assertEqual(len(catalog(getId='doc1_changed')), 1)

        portal_repo.save(doc1, comment='second save')

        portal_repo.revert(doc1, 0)
        rev_doc = fol.doc1_changed
        self.assertEqual(rev_doc.Title(), "v1 of doc1")
        self.assertEqual(len(catalog(getId='doc1')), 0)
        self.assertEqual(len(catalog(getId='doc1_changed')), 1)
        self.assertEqual(len(catalog(Title='v1 of doc1')), 1)

    def test21_RestoreMovedObject(self):
        portal_repo = self.portal.portal_repository
        catalog = self.portal.portal_catalog
        portal_hidhandler = self.portal.portal_historyidhandler
        fol = self.portal.fol
        doc1 = fol.doc1

        # save change no 1
        doc1.setTitle("v1 of doc1")

        portal_repo.applyVersionControl(doc1, comment='first save')
        # save the ``history_id`` to be able to retrieve the object after
        # it's deletion
        history_id = portal_hidhandler.queryUid(doc1)

        doc1.setTitle("v2 of doc1")
        transaction.savepoint()
        fol.manage_renameObject('doc1', 'doc1_changed')
        doc1 = fol.doc1_changed
        doc1.reindexObject()

        self.assertEqual(len(catalog(getId='doc1')), 0)
        self.assertEqual(len(catalog(getId='doc1_changed')), 1)

        portal_repo.save(doc1, comment='second save')
        portal_repo.restore(history_id, selector=0, container=fol)
        # Both documents should now be in place
        res_doc = fol.doc1
        self.assertEqual(res_doc.Title(), "v1 of doc1")
        self.assertEqual(len(catalog(getId='doc1')), 1)
        self.assertEqual(len(catalog(getId='doc1_changed')), 1)
        self.assertEqual(len(catalog(Title='v1 of doc1')), 1)
        self.assertEqual(len(catalog(Title='v2 of doc1')), 1)
        # The reverted document should have a new uid, because an object with
        # the original uid exists
        self.assertFalse(portal_hidhandler.queryUid(res_doc) == history_id)

    def test22_ParentPointerNotVersionedOrRestored(self):
        portal_repo = self.portal.portal_repository
        doc = self.portal.doc

        doc.setTitle("v1")
        # bogus parent
        portal_repo.applyVersionControl(doc)

        doc.setTitle("v2")
        doc.__parent__ = self.portal.fol
        # If an attempt was made to pickle the still wrapped parent object
        # we would see an error here
        portal_repo.save(doc)

        # Change the parent to the correct location
        doc.setTitle("v3")
        doc.__parent__ = self.portal.aq_base

        # revert to check that the current __parent__ is retained on
        # the reverted version
        portal_repo.revert(doc)

        # We have the version that had an erroneous parent pointer, but
        # the current parent pointer has replaced it.
        self.assertEqual(self.portal.doc.Title(), "v2")
        self.assertEqual(self.portal.doc.__parent__, self.portal.aq_base)

    def test23_versioningPreservesFolderAnnotations(self):
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol

        # save change no 1
        fol.setTitle('v1 of fol')
        fol.__annotations__['something'] = True
        portal_repo.applyVersionControl(fol, comment='first save')

        # save change no 2
        fol.setTitle('v2 of fol')
        fol.__annotations__['something'] = False
        portal_repo.save(fol, comment='second save')

        # change no 3 (without saving)
        fol.setTitle('v3 of fol')
        fol.__annotations__['something'] = None
        fol.__annotations__['another_thing'] = True

        # retrieve change 1 and 2
        repo_fol1 = portal_repo.retrieve(fol, 0).object
        repo_fol2 = portal_repo.retrieve(fol, 1).object

        # Test values on the repository copies and the working copy
        self.assertEqual(repo_fol1.__annotations__['something'], True)
        self.assertEqual(repo_fol2.__annotations__['something'], False)
        self.assertEqual(fol.__annotations__['something'], None)
        self.assertEqual(repo_fol2.__annotations__.get('another_thing',
                                                           None), None)

        # Test that revert brings in the original annotation
        portal_repo.revert(fol)
        self.assertEqual(fol.__annotations__['something'], False)
        self.assertEqual(fol.__annotations__.get('another_thing', None),
                             None)

        portal_repo.revert(fol, 0)
        self.assertEqual(fol.__annotations__['something'], True)

    def test24_versioningPreservesFolderOrder(self):
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol
        doc2 = fol['doc2']

        # save change no 1
        fol.setTitle('v1 of fol')
        portal_repo.applyVersionControl(fol, comment='first save')

        # save change no 2
        fol.setTitle('v2 of fol')
        fol.moveObjectsToTop(['doc2'])

        self.assertEqual(fol.objectIds()[0], 'doc2')

        working_ids = fol.objectIds()

        # Test that a retrieve provides the order and content from
        # the working copy on the repo copy
        repo_fol1 = portal_repo.retrieve(fol, 0).object
        self.assertEqual(repo_fol1.objectIds(), working_ids)

        # Test that a revert preserves the order from the working copy
        portal_repo.revert(fol)
        self.assertEqual(fol.objectIds(), working_ids)

        # See how we interact with delete
        fol.invokeFactory('Document', 'doc3')
        fol.moveObjectsToTop(['doc3'])
        fol.manage_delObjects(['doc2'])
        transaction.savepoint(optimistic=True)

        working_ids = fol.objectIds()
        doc3 = fol['doc3']
        portal_repo.revert(fol)

        # Test that we kept the ids from working copy, kept the new child
        # restored the deleted child
        self.assertEqual(fol.objectIds(), working_ids)
        self.assertEqual(fol.objectIds()[0], 'doc3')
        self.assertEqual(getattr(fol, 'doc2', None), None)
        self.assertEqual(fol['doc3'], doc3)

        # Test the BTreeFolder internals
        self.assertEqual(fol._tree.get('doc2', None), None)
        self.assertEqual(fol._tree['doc3'], doc3)
        self.assertEqual(fol._count(), 2)
        self.assertEqual(fol._mt_index[doc2.meta_type].get('doc2', None),
                             None)
        self.assertEqual(fol._mt_index[doc3.meta_type]['doc3'], 1)

    def test25_versioningRestoresInsideRefsFolderOrder(self):
        # Enable OMInsideChildrensModifier
        portal_modifier = self.portal.portal_modifier
        portal_modifier.edit("OMOutsideChildrensModifier", enabled=False,
                             condition="python: False")
        portal_modifier.edit("OMInsideChildrensModifier", enabled=True,
                             condition="python: portal_type=='Folder'")

        portal_repo = self.portal.portal_repository
        fol = self.portal.fol

        # save change no 1
        fol.setTitle('v1 of fol')
        fol.invokeFactory('Document', 'doc3')
        fol.invokeFactory('Document', 'doc4')
        portal_repo.applyVersionControl(fol, comment='first save')

        orig_order = fol.objectIds()

        fol.setTitle('v2 of fol')
        fol.moveObjectsToTop(['doc2'])

        self.assertEqual(fol.objectIds()[0], 'doc2')

        # Test that a retrieve uses the order from the repo copy
        repo_fol1 = portal_repo.retrieve(fol, 0).object
        self.assertEqual(fol.objectIds()[0], 'doc2')
        self.assertNotEqual(fol.objectIds(), orig_order)
        self.assertEqual(repo_fol1.objectIds()[0], 'doc1')

        # Test that a revert restores the order and objects from the
        # repo copy
        portal_repo.revert(fol)
        self.assertEqual(fol.objectIds()[0], 'doc1')
        self.assertEqual(fol.objectIds(), orig_order)

        # See how we interact with some adds deletes and reorders
        fol.invokeFactory('Document', 'doc5')
        fol.moveObjectsToTop(['doc3'])
        fol.moveObjectsToTop(['doc4'])
        fol.manage_delObjects(['doc2'])
        processQueue()
        transaction.savepoint(optimistic=True)
        doc3 = fol['doc3']
        doc4 = fol['doc4']

        self.assertNotEqual(fol.objectIds(), orig_order)

        repo_fol1 = portal_repo.retrieve(fol, 0).object

        # Test that a retrieve uses the repository order and items,
        # but does not affect the working copy
        repo_fol1 = portal_repo.retrieve(fol, 0).object
        self.assertEqual(repo_fol1.objectIds(), orig_order)
        self.assertNotEqual(getattr(repo_fol1, 'doc2', None), None)
        self.assertEqual(getattr(repo_fol1, 'doc5', None), None)

        self.assertNotEqual(fol.objectIds(), orig_order)
        self.assertEqual(fol.objectIds()[0], 'doc4')
        self.assertEqual(fol.objectIds()[1], 'doc3')
        self.assertEqual(fol['doc3'], doc3)
        self.assertEqual(fol['doc4'], doc4)
        self.assertEqual(getattr(fol, 'doc2', None), None)
        self.assertNotEqual(getattr(fol, 'doc5', None), None)

        # Test that a revert restores the missing child from the repo
        # copy, removed the newly created child and restored the order
        portal_repo.revert(fol)

        self.assertEqual(list(fol.objectIds()), orig_order)
        self.assertEqual(getattr(fol, 'doc5', None), None)

        # Test the BTreeFolder internals
        self.assertEqual(fol._tree.get('doc5', None), None)
        self.assertEqual(fol._count(), 4)
        self.assertEqual(fol._mt_index[doc3.meta_type].get('doc5', None),
                             None)
        self.assertEqual(fol._tree['doc3'], fol['doc3'].aq_base)
        self.assertEqual(fol._mt_index[doc3.meta_type]['doc3'], 1)

    def test26_RegistryBasesNotVersionedOrRestored(self):
        portal_repo = self.portal.portal_repository
        fol = self.portal.fol

        fol.setTitle("v1")
        # Make it a component registry with bases
        base = aq_base(self.portal.getSiteManager())
        components = PersistentComponents()
        components.__bases__ = (base,)
        fol.setSiteManager(components)
        portal_repo.applyVersionControl(fol)

        broken_iface = broken.find_global(
            'never_gonna_be_real', 'IMissing',
            Broken=ZODB.interfaces.IBroken, type=InterfaceClass)
        sys.modules[broken_iface.__module__] = module = imp.new_module(
            broken_iface.__module__)
        module.IMissing = broken_iface

        # add a broken registrsation but do a savepoint before
        # breaking the interfaces to simulate a broken registrion from
        # a previous commit
        base.registerUtility(component=None, provided=broken_iface)
        transaction.savepoint(optimistic=True)
        del sys.modules[broken_iface.__module__]

        fol.setTitle("v2")

        # If an attempt was made to pickle the parent registry's
        # broken registration we would see an error here
        portal_archivist = self.portal.portal_archivist
        portal_archivist._cloneByPickle(fol)

        self.assertEqual(self.portal.fol.Title(), "v2")
        self.assertTrue(
            self.portal.fol.getSiteManager().__bases__[0] is base)
