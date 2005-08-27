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

$Id: test_CopyModifyMergeRepositoryTool.py,v 1.17 2005/06/22 10:43:46 gregweb Exp $
"""

import os, sys
import time
import copy
from StringIO import StringIO
from cPickle import Pickler, Unpickler
from pickle import dumps, loads

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# BBB
try:
    import transaction
except ImportError:
    from Products.CMFEditions.bbb import transaction

from Testing import ZopeTestCase
from Products.CMFTestCase import CMFTestCase

from Interface.Verify import verifyObject
from Acquisition import aq_base

from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import getToolByName

from Products.CMFEditions.Extensions import Install
from Products.CMFEditions.interfaces.IRepository import ICopyModifyMergeRepository
from Products.CMFEditions.interfaces.IRepository import IVersionData
from Products.CMFEditions.interfaces.IArchivist import ArchivistError

from Products.PloneTestCase import PloneTestCase
from Products.CMFEditions.tests import installProduct

PloneTestCase.setupPloneSite()
ZopeTestCase.installProduct('CMFUid')
ZopeTestCase.installProduct('CMFEditions')

ZopeTestCase.installProduct('Zelenium')
ZopeTestCase.installProduct('PloneSelenium')

portal_owner = PloneTestCase.portal_owner
portal_name = PloneTestCase.portal_name
default_user = PloneTestCase.default_user

from DummyTools import DummyArchivist

class TestCopyModifyMergeRepositoryTool(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])

        # add an additional user
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')

        # add test data
        installProduct(self.portal, 'CMFEditions')
        installProduct(self.portal, 'PloneSelenium', optional=True)
        
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

    def test00_interface(self):
        portal_repository = self.portal.portal_repository
        portal_archivist = self.portal.portal_archivist
        doc = self.portal.doc

        # test the tools interface conformance
        verifyObject(ICopyModifyMergeRepository, portal_repository)

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
        
        vdata = portal_archivist.retrieve(doc, 0)
        
        self.assertEqual(vdata.data.object.text, 'text v1')
        vdata = portal_archivist.retrieve(doc, 1)
        self.assertEqual(vdata.data.object.text, 'text v2')

    def test02_retrieve(self):
        portal_repository = self.portal.portal_repository
        portal_archivist = self.portal.portal_archivist
        doc = self.portal.doc
        
        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        doc.text = 'text v2'
        portal_repository.save(doc, comment='save no 2')
        
        vdata = portal_repository.retrieve(doc, selector=0)
        verifyObject(IVersionData, vdata)
        self.assertEqual(vdata.object.text, 'text v1')
        vdata = portal_repository.retrieve(doc, selector=1)
        self.assertEqual(vdata.object.text, 'text v2')
        
    def test03_recursiveRevertOfOutsideObject(self):
        portal_repository = self.portal.portal_repository
        portal_archivist = self.portal.portal_archivist
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
        
        # XXX lets look at that later
#        self.assertEqual(self.portal.fol.doc3_outside, doc3_outside)
        
        self.assertEqual(fol.title, 'fol title v1')
        self.assertEqual(doc3_outside.title, 
                        'doc3_outside title text v2')

    def test04_isUptoDate(self):
        portal_repository = self.portal.portal_repository
        portal_archivist = self.portal.portal_archivist
        doc = self.portal.doc
        
        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        self.assertEqual(portal_repository.isUpToDate(doc), True)
        time.sleep(2)
        doc.text = 'text v2'
        doc.notifyModified()
        self.assertEqual(portal_repository.isUpToDate(doc), False)

    def test05_getHistory(self):
        portal_repository = self.portal.portal_repository
        portal_archivist = self.portal.portal_archivist
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

    def test06_getObjectType(self):
        portal_repository = self.portal.portal_repository
        portal_hidhandler = self.portal.portal_historyidhandler
        
        doc = self.portal.doc
        portal_repository.applyVersionControl(doc, comment='save no 1')
        history_id = portal_hidhandler.queryUid(doc)
        content_type = portal_repository.getObjectType(history_id)
        self.assertEqual(content_type, 'Document')

        link = self.portal.link
        portal_repository.applyVersionControl(link, comment='save no 1')
        history_id = portal_hidhandler.queryUid(link)
        content_type = portal_repository.getObjectType(history_id)
        self.assertEqual(content_type, 'Link')

    def test07_retrieveWithNoMoreExistentObject(self):
        portal_repository = self.portal.portal_repository
        portal_archivist = self.portal.portal_archivist
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
        self.portal.manage_delObjects(ids=['doc'])
        doc_type = portal_repository.getObjectType(history_id)
        self.portal.invokeFactory(doc_type, 'XXX')
        doc = self.portal.XXX
        portal_hidhandler.setUid(doc, history_id, check_uniqueness=True)
        vdata = portal_repository.retrieve(doc, selector=0)
        verifyObject(IVersionData, vdata)
        self.assertEqual(vdata.object.text, 'text v1')
        vdata = portal_repository.retrieve(doc, selector=1)
        self.assertEqual(vdata.object.text, 'text v2')
        


class TestRepositoryWithDummyArchivist(TestCopyModifyMergeRepositoryTool):

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
        # XXX the result depends on a history id handler returning 
        #     numbers staring with 1 (see 'hid')
        alog_str = portal_archivist.get_log()
        expected = """
prepare fol: hid=1, refs=(doc1_inside, doc2_inside, doc3_outside)
  prepare doc1_inside: hid=2
  save    doc1_inside: hid=2, isreg=False, auto=True
  prepare doc2_inside: hid=3
  save    doc2_inside: hid=3, isreg=False, auto=True
save    fol: hid=1, irefs=({hid:2, vid:0}, {hid:3, vid:0}), orefs=({hid:None, vid:-1}), isreg=False, auto=True

prepare fol: hid=1, refs=(doc1_inside, doc2_inside, doc3_outside)
  prepare doc1_inside: hid=2
  save    doc1_inside: hid=2, isreg=True, auto=False
  prepare doc2_inside: hid=3
  save    doc2_inside: hid=3, isreg=True, auto=False
save    fol: hid=1, irefs=({hid:2, vid:1}, {hid:3, vid:1}), orefs=({hid:None, vid:-1}), isreg=True, auto=False"""
        
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

        retr = portal_repository.retrieve(fol, 0)

        # check recursive retrieve
        alog_str = portal_archivist.get_log()

        expected = """retrieve fol: hid=1, selector=0
retrieve doc1_inside: hid=2, selector=0
retrieve doc2_inside: hid=3, selector=0"""
        self.assertEqual(alog_str, expected)

        # check result
        self.assertEqual(retr.object.title, 'fol title v1')
        self.assertEqual(retr.object.doc1_inside.title,
                        'doc1_inside title text v1')
        self.assertEqual(retr.object.doc2_inside.title,
                        'doc2_inside title text v1')
        self.assertEqual(retr.object.doc3_outside.title,
                        'doc3_outside title text v2')


class TestRegressionTests(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])
        installProduct(self.portal, 'CMFEditions')
        installProduct(self.portal, 'PloneSelenium', optional=True)

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
        portal_archivist = self.portal.portal_archivist
        doc = self.portal.doc
        doc.text = 'text v1'
        portal_repository.applyVersionControl(doc, comment='save no 1')
        doc.text = 'text v2'
        transaction.commit(1)
        self.portal.manage_renameObject(doc.getId(), 'newdoc',)
        portal_repository.save(doc, comment='save no 2')
        portal_repository.revert(doc, 0)
        self.assertEqual(doc.getId(), 'newdoc')
        self.failUnless('newdoc' in self.portal.objectIds())


if __name__ == '__main__':
    framework()
else:
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestCopyModifyMergeRepositoryTool))
        suite.addTest(makeSuite(TestRepositoryWithDummyArchivist))
        suite.addTest(makeSuite(TestRegressionTests))
        return suite
