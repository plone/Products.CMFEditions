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

$Id: test_ArchivistTool.py,v 1.10 2005/02/25 22:04:00 tomek1024 Exp $
"""

from Products.PloneTestCase import PloneTestCase
PloneTestCase.setupPloneSite()

from zope.interface.verify import verifyObject

from Products.CMFEditions.interfaces.IArchivist import IArchivist
from Products.CMFEditions.interfaces.IArchivist import IPurgeSupport

from DummyTools import DummyModifier
from DummyTools import DummyHistoryIdHandler
from DummyTools import MemoryStorage
from DummyTools import notifyModified
from DummyTools import FolderishContentObjectModifier


class TestArchivistToolMemoryStorage(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.setRoles(['Manager',])
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')
        self.portal.invokeFactory('Document', 'doc')
        self.portal.invokeFactory('Folder', 'fol')
        self.portal.fol.invokeFactory('Document', 'doc1_inside')
        self.portal.fol.invokeFactory('Document', 'doc2_inside')
        self.portal.fol.invokeFactory('Document', 'doc3_outside')
        tools = (
            DummyModifier(),
            DummyHistoryIdHandler(),
            )
        for tool in tools:
            self._setDummyTool(tool)

        self.installStorageTool()

        # delete purge policy if there is one installed
        try:
            del self.portal.portal_purgepolicy
        except AttributeError:
            pass

    def installStorageTool(self):
        self._setDummyTool(MemoryStorage())

    def _setDummyTool(self, tool):
        setattr(self.portal, tool.getId(), tool)

    def test00_interface(self):
        portal_archivist = self.portal.portal_archivist
        verifyObject(IArchivist, portal_archivist)
        verifyObject(IPurgeSupport, portal_archivist)

    def test01_registerAttachesAHistoryId(self):
        portal_archivist = self.portal.portal_archivist
        portal_historyidhandler = self.portal.portal_historyidhandler
        portal_historiesstorage = self.portal.portal_historiesstorage
        doc = self.portal.doc
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        portal_archivist.register(prep)
        history_id = portal_historyidhandler.queryUid(doc)
        self.failUnless(history_id)

    def test02_retrieve(self):
        portal_archivist = self.portal.portal_archivist
        portal_historyidhandler = self.portal.portal_historyidhandler
        portal_historiesstorage = self.portal.portal_historiesstorage
        doc = self.portal.doc
        doc.text = 'text v1'
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        portal_archivist.register(prep)
        doc.text = 'text v2'
        prep = portal_archivist.prepare(doc, app_metadata='save number 2')
        portal_archivist.save(prep)
        vdata = portal_archivist.retrieve(obj=doc, selector=0, preserve=('gaga', 'gugus'))
        retr_doc = vdata.data.object
        retr_meta = vdata.app_metadata
        doc_histid = portal_historyidhandler.queryUid(doc)
        retr_histid = portal_historyidhandler.queryUid(retr_doc)
        self.assertEqual(doc_histid, retr_histid)
        # check if correct version retrieved and working object unchanged
        self.assertEqual(retr_doc.text , 'text v1')
        self.assertEqual(retr_meta , 'save number 1')
        self.assertEqual(doc.text , 'text v2')
        self.assertEqual(len(vdata.preserved_data), 2)
        self.assertEqual(vdata.preserved_data['gaga'], 'gaga')
        self.assertEqual(vdata.preserved_data['gugus'], 'gugus')

    def test03_retrieveById(self):
        portal_archivist = self.portal.portal_archivist
        portal_historyidhandler = self.portal.portal_historyidhandler
        portal_historiesstorage = self.portal.portal_historiesstorage
        doc = self.portal.doc
        doc.text = 'text v1'
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        portal_archivist.register(prep)
        doc.text = 'text v2'
        prep = portal_archivist.prepare(doc, app_metadata='save number 2')
        portal_archivist.save(prep)
        doc_histid = portal_historyidhandler.queryUid(doc)
        vdata = portal_archivist.retrieve(history_id=doc_histid, selector=0,
                                          preserve=('gaga', 'gugus'))
        retr_doc = vdata.data.object
        retr_meta = vdata.app_metadata
        # check if correct version retrieved and working object unchanged
        self.assertEqual(retr_doc.text , 'text v1')
        self.assertEqual(retr_meta , 'save number 1')
        self.assertEqual(doc.text , 'text v2')
        self.assertEqual(len(vdata.preserved_data), 2)
        self.assertEqual(vdata.preserved_data['gaga'], 'gaga')
        self.assertEqual(vdata.preserved_data['gugus'], 'gugus')

    def test04_getHistory(self):
        portal_archivist = self.portal.portal_archivist
        portal_historyidhandler = self.portal.portal_historyidhandler
        portal_historiesstorage = self.portal.portal_historiesstorage
        doc = self.portal.doc

        doc.text = 'text v1'
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        portal_archivist.register(prep)

        doc.text = 'text v2'
        prep = portal_archivist.prepare(doc, app_metadata='save number 2')
        portal_archivist.save(prep)

        history = portal_archivist.getHistory(doc)

        self.assertEqual(len(history), 2)
        # check if timestamp and principal available
        self.failUnless(history[0].sys_metadata['timestamp'])
        self.failUnless(history[0].sys_metadata['principal'])
        # check if correct data and metadata retrieved
        self.assertEqual(history[0].data.object.text, 'text v1')
        self.assertEqual(history[0].app_metadata, 'save number 1')
        self.assertEqual(history[1].data.object.text, 'text v2')
        self.assertEqual(history[1].app_metadata, 'save number 2')

    def test05_iterateOverHistory(self):
        portal_archivist = self.portal.portal_archivist
        doc = self.portal.doc

        doc.text = 'text v1'
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        portal_archivist.register(prep)

        doc.text = 'text v2'
        prep = portal_archivist.prepare(doc, app_metadata='save number 2')
        portal_archivist.save(prep)

        doc.text = 'text v3'
        prep = portal_archivist.prepare(doc, app_metadata='save number 3')
        portal_archivist.save(prep)

        counter = 0

        for vdata in portal_archivist.getHistory(doc):
            counter += 1
            self.assertEqual(vdata.data.object.text, 'text v%s' % counter)
            self.assertEqual(vdata.app_metadata, 'save number %s' % counter)

    def test06_getHistoryById(self):
        portal_archivist = self.portal.portal_archivist
        portal_historyidhandler = self.portal.portal_historyidhandler
        portal_historiesstorage = self.portal.portal_historiesstorage
        doc = self.portal.doc

        doc.text = 'text v1'
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        portal_archivist.register(prep)

        doc.text = 'text v2'
        prep = portal_archivist.prepare(doc, app_metadata='save number 2')
        portal_archivist.save(prep)

        doc_histid = portal_historyidhandler.queryUid(doc)
        history = portal_archivist.getHistory(history_id=doc_histid)

        self.assertEqual(len(history), 2)
        # check if timestamp and principal available
        self.failUnless(history[0].sys_metadata['timestamp'])
        self.failUnless(history[0].sys_metadata['principal'])
        # check if correct data and metadata retrieved
        self.assertEqual(history[0].data.object.text, 'text v1')
        self.assertEqual(history[0].app_metadata, 'save number 1')
        self.assertEqual(history[1].data.object.text, 'text v2')
        self.assertEqual(history[1].app_metadata, 'save number 2')

    def test07_prepareObjectWithReferences(self):
        # test with a different modifier
        self._setDummyTool(FolderishContentObjectModifier())

        portal_archivist = self.portal.portal_archivist
        portal_hidhandler = self.portal.portal_historyidhandler
        IVersionAwareReference = portal_archivist.interfaces.IVersionAwareReference
        fol = self.portal.fol
        fol.title = "BLOB title ..."
        doc1_inside = fol.doc1_inside
        doc2_inside = fol.doc2_inside
        doc3_outside = fol.doc3_outside

        doc1_inside.text = 'doc1_inside: inside reference'
        doc2_inside.text = 'doc2_inside: inside reference'
        doc3_outside.text = 'doc3_outside: outside reference'

        prep = portal_archivist.prepare(fol, app_metadata='save number 1')

        self.assertEqual(fol, prep.original.object)

        # it is important that the clones returned reference info contain
        # references to the outgoing references and the python refs are
        # replaced by 'IVersionAwareRefrence' objects
        inside_refs = prep.clone.inside_refs
        outside_refs = prep.clone.outside_refs
        self.assertEqual(len(inside_refs), 2)
        self.assertEqual(len(outside_refs), 1)
        refs = [ref.getAttribute() for ref in inside_refs+outside_refs]
        for ref in refs:
            self.failUnless(IVersionAwareReference.providedBy(ref))
        cloneValues = prep.clone.object.objectValues()
        for sub in cloneValues:
            self.failUnless(sub in refs)

        # it is important that the originals returned reference info contain
        # references to the outgoing references
        inside_orefs = prep.original.inside_refs
        outside_orefs = prep.original.outside_refs
        self.assertEqual(len(inside_orefs), 2)
        self.assertEqual(len(outside_orefs), 1)
        refs = inside_orefs+outside_orefs
        originalValues = prep.original.object.objectValues()

        for sub in originalValues:
            self.failUnless(sub in refs)

        # the clones and the originals refs must also reference the
        # "same" object
        self.assertEqual(prep.clone.object.objectIds(),
                         prep.original.object.objectIds())

        self.assertEqual(len(prep.referenced_data), 1)
        self.failUnless(prep.referenced_data['title'] is fol.title)

        self.assertEqual(prep.metadata['app_metadata'], 'save number 1')
        self.failUnless('timestamp' in prep.metadata['sys_metadata'])
        self.failUnless('principal' in prep.metadata['sys_metadata'])

        self._setDummyTool(DummyModifier())

    def test08_retrieveWithReferences(self):
        # test with a different modifier
        self._setDummyTool(FolderishContentObjectModifier())

        portal_archivist = self.portal.portal_archivist
        portal_hidhandler = self.portal.portal_historyidhandler
        IVersionAwareReference = portal_archivist.interfaces.IVersionAwareReference
        fol = self.portal.fol
        fol.title = "BLOB title ..."
        doc1_inside = fol.doc1_inside
        doc2_inside = fol.doc2_inside
        doc3_outside = fol.doc3_outside

        doc1_inside.text = 'doc1_inside: inside reference'
        doc2_inside.text = 'doc2_inside: inside reference'
        doc3_outside.text = 'doc3_outside: outside reference'

        prep = portal_archivist.prepare(fol, app_metadata='save number 1')

        # just set the info to some value before save to test if the
        # reference stuff is saved and retrieved correctly
        inside_refs = prep.clone.inside_refs
        outside_refs = prep.clone.outside_refs
        refs = [ref.getAttribute() for ref in inside_refs+outside_refs]
        for ref in refs:
            ref.info = refs.index(ref)

        portal_archivist.save(prep, autoregister=True)

        retr = portal_archivist.retrieve(fol)

        # check metadata
        self.assertEqual(retr.app_metadata, 'save number 1')
        self.failUnless('timestamp' in retr.sys_metadata)
        self.failUnless('principal' in retr.sys_metadata)

        # check the references
        inside_refs = retr.data.inside_refs
        outside_refs = retr.data.outside_refs
        self.assertEqual(len(inside_refs), 2)
        self.assertEqual(len(outside_refs), 1)
        refs = [ref.getAttribute() for ref in inside_refs+outside_refs]
        for ref in refs:
            self.failUnless(IVersionAwareReference.providedBy(ref))
            # check info value (see note above)
            self.assertEquals(ref.info, refs.index(ref))

    def test09_isUpToDate(self):
        doc = self.portal.doc
        portal_archivist = self.portal.portal_archivist
        doc.text = 'text v1'
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        v1 = portal_archivist.register(prep)

        self.failUnless(portal_archivist.isUpToDate(obj=doc))
        self.failUnless(portal_archivist.isUpToDate(obj=doc, selector=v1))

        doc.text = 'text v2'
        notifyModified(doc)
        self.failIf(portal_archivist.isUpToDate(obj=doc))

        prep = portal_archivist.prepare(doc, app_metadata='save number 2')
        v2 = portal_archivist.save(prep)

        self.failUnless(portal_archivist.isUpToDate(obj=doc))
        self.failUnless(portal_archivist.isUpToDate(obj=doc, selector=v2))
        self.failIf(portal_archivist.isUpToDate(obj=doc, selector=v1))

    def test09_getHistoryMetadata(self):
        portal_archivist = self.portal.portal_archivist
        doc = self.portal.doc

        doc.text = 'text v1'
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        portal_archivist.register(prep)

        doc.text = 'text v2'
        prep = portal_archivist.prepare(doc, app_metadata='save number 2')
        portal_archivist.save(prep)

        history = portal_archivist.getHistoryMetadata(doc)

        self.assertEqual(len(history), 2)
        # check if timestamp and principal available
        self.failUnless(history.retrieve(1)['metadata']['sys_metadata']['timestamp'])
        self.failUnless(history.retrieve(0)['metadata']['sys_metadata']['principal'])
        # check if correct data and metadata retrieved
        self.assertEqual(history.retrieve(0)['metadata']['app_metadata'], 'save number 1')
        self.assertEqual(history.retrieve(1)['metadata']['app_metadata'], 'save number 2')

    def test09_getHistoryMetadata_byId(self):
        portal_archivist = self.portal.portal_archivist
        doc = self.portal.doc

        doc.text = 'text v1'
        prep = portal_archivist.prepare(doc, app_metadata='save number 1')
        portal_archivist.register(prep)

        doc.text = 'text v2'
        prep = portal_archivist.prepare(doc, app_metadata='save number 2')
        portal_archivist.save(prep)

        # retrieve the history by history id
        history = portal_archivist.getHistoryMetadata(history_id=1)

        self.assertEqual(len(history), 2)
        # check if timestamp and principal available
        self.failUnless(history.retrieve(1)['metadata']['sys_metadata']['timestamp'])
        self.failUnless(history.retrieve(0)['metadata']['sys_metadata']['principal'])
        # check if correct data and metadata retrieved
        self.assertEqual(history.retrieve(0)['metadata']['app_metadata'], 'save number 1')
        self.assertEqual(history.retrieve(1)['metadata']['app_metadata'], 'save number 2')

class TestArchivistToolZStorage(TestArchivistToolMemoryStorage):

   def installStorageTool(self):
       """Test with a real ZODB storage overriding the storage installation
          in the super class.
       """
       # reset the shadow storage to avoid the effect of any versions created
       # during portal setup
       self.portal.portal_historiesstorage._shadowStorage = None


from unittest import TestSuite, makeSuite
def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestArchivistToolMemoryStorage))
    suite.addTest(makeSuite(TestArchivistToolZStorage))
    return suite
