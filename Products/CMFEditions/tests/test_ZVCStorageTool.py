#########################################################################
# Copyright (c) 2004, 2005 Alberto Berti, Gregoire Weber,
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

$Id: test_ZVCStorageTool.py,v 1.12 2005/02/24 21:53:44 tomek1024 Exp $
"""

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Interface.Verify import verifyObject
from Acquisition import aq_base

from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager

from Products.CMFEditions.Extensions import Install
from Products.CMFEditions.interfaces.IStorage import IStorage
from Products.CMFEditions.interfaces.IPurgeSupport import IPurgeSupport
from Products.CMFEditions.interfaces.IStorage import StorageUnregisteredError

from Products.CMFEditions import UniqueIdHandlerTool
from Products.CMFEditions import ModifierRegistryTool
from Products.CMFEditions import ArchivistTool
from Products.CMFEditions.ArchivistTool import ObjectData
from Products.CMFEditions import ZVCStorageTool
from Products.CMFEditions import CopyModifyMergeRepositoryTool
from DummyTools import MemoryStorage
from DummyTools import Dummy as Dummy
from DummyTools import notifyModified

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

class DummyOM(ObjectManager):
    pass

class TestZVCStorageTool(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])
        installProduct(self.portal, 'CMFEditions')
        # add an additional user
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')

        # add the Editions Tool (this way we test the 'Install' script!)
        tools = (
            UniqueIdHandlerTool.UniqueIdHandlerTool,
            ModifierRegistryTool.ModifierRegistryTool,
            ArchivistTool.ArchivistTool,
            CopyModifyMergeRepositoryTool.CopyModifyMergeRepositoryTool,
        )

    def installStorageTool(self):
        """Install your storage tool at this point"""
        CMFEditions = self.portal.manage_addProduct['CMFEditions']
        CMFEditions.manage_addTool(ZVCStorageTool.ZVCStorageTool.meta_type)

    def buildMetadata(self, comment):
        return {'sys_metadata': {'comment': comment}}

    def getComment(self, metadata):
        return metadata['sys_metadata']['comment']

    def test00_interface(self):
        portal_storage = self.portal.portal_historiesstorage

        # test interface conformance
        verifyObject(IStorage, portal_storage)
        verifyObject(IPurgeSupport, portal_storage)

    def test01_saveAfterRegisteringDoesNotRaiseException(self):
        portal_storage = self.portal.portal_historiesstorage
        obj = Dummy()

        portal_storage.register(1, ObjectData(obj), metadata=self.buildMetadata('saved'))
        portal_storage.save(1, ObjectData(obj), metadata=self.buildMetadata('saved'))

    def test02_saveUnregisteredObjectRaisesException(self):
        portal_storage = self.portal.portal_historiesstorage
        obj = Dummy()

        self.assertRaises(StorageUnregisteredError,
                          portal_storage.save,
                          1, ObjectData(obj), metadata=self.buildMetadata('saved'))

    def test03_saveAndRetrieve(self):
        portal_storage = self.portal.portal_historiesstorage

        obj1 = Dummy()
        obj1.text = 'v1 of text'
        portal_storage.register(1, ObjectData(obj1), metadata=self.buildMetadata('saved v1'))

        obj2 = Dummy()
        obj2.text = 'v2 of text'
        portal_storage.save(1, ObjectData(obj2), metadata=self.buildMetadata('saved v2'))
        
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=0)
        self.assertEqual(retrieved_obj.object.object.text, 'v1 of text')
        self.assertEqual(self.getComment(retrieved_obj.metadata), 'saved v1')
        
        # the same with ``retrieveUnsubstituted``
        retrieved_obj = portal_storage.retrieveUnsubstituted(history_id=1, 
                                                             selector=0)
        self.assertEqual(retrieved_obj.object.object.text, 'v1 of text')
        self.assertEqual(self.getComment(retrieved_obj.metadata), 'saved v1')
        
        # just check if first save wasn't a double save
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=1)
        self.assertEqual(retrieved_obj.object.object.text, 'v2 of text')
        self.assertEqual(self.getComment(retrieved_obj.metadata), 'saved v2')

    def test04_getHistory(self):
        portal_storage = self.portal.portal_historiesstorage
        
        obj1 = Dummy()
        obj1.text = 'v1 of text'
        portal_storage.register(1, ObjectData(obj1), metadata=self.buildMetadata('saved v1'))
        
        obj2 = Dummy()
        obj2.text = 'v2 of text'
        portal_storage.save(1, ObjectData(obj2), metadata=self.buildMetadata('saved v2'))
        
        obj3 = Dummy()
        obj3.text = 'v3 of text'
        portal_storage.save(1, ObjectData(obj3), metadata=self.buildMetadata('saved v3'))
        
        # XXX need to test for history[selector].data and history[selector].metadata
        history = portal_storage.getHistory(history_id=1)
        
        self.assertEquals(len(history), 3)
        
        self.assertEquals(history[0].object.object.text, obj1.text)
        self.assertEqual(self.getComment(history[0].metadata), 'saved v1')
        self.assertEquals(history[1].object.object.text, obj2.text)
        self.assertEqual(self.getComment(history[1].metadata), 'saved v2')
        self.assertEquals(history[2].object.object.text, obj3.text)
        self.assertEqual(self.getComment(history[2].metadata), 'saved v3')

    def test05_iterateOverHistory(self):
        portal_storage = self.portal.portal_historiesstorage
        
        obj1 = Dummy()
        obj1.text = 'v1 of text'
        portal_storage.register(1, ObjectData(obj1), metadata=self.buildMetadata('saved v1'))
        
        obj2 = Dummy()
        obj2.text = 'v2 of text'
        portal_storage.save(1, ObjectData(obj2), metadata=self.buildMetadata('saved v2'))
        
        obj3 = Dummy()
        obj3.text = 'v3 of text'
        portal_storage.save(1, ObjectData(obj3), metadata=self.buildMetadata('saved v3'))
        
        counter = 0
        for vdata in portal_storage.getHistory(history_id=1):
            counter += 1
            self.assertEqual(vdata.object.object.text, 'v%s of text' % counter)
            self.assertEqual(self.getComment(vdata.metadata), 'saved v%s' % counter)

    def test06_checkObjectManagerIntegrity(self):
        portal_storage = self.portal.portal_historiesstorage
        
        om = DummyOM()
        sub1 = Dummy()
        sub2 = Dummy()
        om._setObject('sub1', sub1)
        om._setObject('sub2', sub2)
        self.assertEqual(len(om.objectIds()), 2)
        portal_storage.register(1, ObjectData(om), metadata=self.buildMetadata('saved v1'))
        vdata = portal_storage.retrieve(history_id=1, selector=0)
        retrieved_om = vdata.object
        self.assertEqual(len(retrieved_om.object.objectIds()), 2)

    def test07_getModificationDate(self):
        portal_storage = self.portal.portal_historiesstorage
        obj = Dummy()
        v1_modified = obj.modified()
        v1 = portal_storage.register(history_id=1, object=ObjectData(obj), metadata=self.buildMetadata('saved v1'))
        self.assertEqual(v1_modified, portal_storage.getModificationDate(history_id=1))
        self.assertEqual(v1_modified, portal_storage.getModificationDate(history_id=1, selector=v1))

        #storage never gets the same object twice, because the archivist always generates another copy on save,
        #which then have a diffrent python id.

        #simulate object copy
        notifyModified(obj)
        obj = Dummy()
        v2_modified = obj.modified()
        v2 = portal_storage.save(history_id=1, object=ObjectData(obj), metadata=self.buildMetadata('saved v2'))
        self.assertNotEquals(v1, v2)
        self.assertEqual(v2_modified, portal_storage.getModificationDate(history_id=1))
        self.assertEqual(v2_modified, portal_storage.getModificationDate(history_id=1, selector=v2))
        self.assertEqual(v1_modified, portal_storage.getModificationDate(history_id=1, selector=v1))

    def test08_lengthAfterHavingPurgedAVersion(self):
        portal_storage = self.portal.portal_historiesstorage
        
        obj1 = Dummy()
        obj1.text = 'v1 of text'
        portal_storage.register(1, ObjectData(obj1), metadata=self.buildMetadata('saved v1'))
        
        obj2 = Dummy()
        obj2.text = 'v2 of text'
        portal_storage.save(1, ObjectData(obj2), metadata=self.buildMetadata('saved v2'))
        
        obj3 = Dummy()
        obj3.text = 'v3 of text'
        portal_storage.save(1, ObjectData(obj3), metadata=self.buildMetadata('saved v3'))
        
        # purge a version
        portal_storage.purge(1, 1, comment='purged v2')
        
        lenWith = portal_storage.getLength(1, ignorePurged=False)
        self.assertEqual(lenWith, 3)
        lenWithout = portal_storage.getLength(1, ignorePurged=True)
        self.assertEqual(lenWithout, 2)
        
        # purge again the same version (should not change the purge count)
        portal_storage.purge(1, 1, comment="purged v2")
        
        lenWith = portal_storage.getLength(1, ignorePurged=False)
        self.assertEqual(lenWith, 3)
        lenWithout = portal_storage.getLength(1, ignorePurged=True)
        self.assertEqual(lenWithout, 2)

        # the same with ``retrieveUnsubstituted``
        retrieved_obj = portal_storage.retrieveUnsubstituted(history_id=1, 
                                                             selector=1)
        self.assertEqual(retrieved_obj.object.reason, "purged")
        self.assertEqual(self.getComment(retrieved_obj.metadata), "purged v2")
        

    def _test09_xxx(self):
        history = portal_storage.getHistory(history_id=1)
        self.assertEqual(len(history), 2)
        vdata = history[0]
        self.assertEqual(vdata.object.object.text, 'v1 of text')
        self.assertEqual(self.getComment(vdata.metadata), 'saved v%s' % counter)
        vdata = history[1]
        self.assertEqual(vdata.object.object.text, 'v3 of text')
        self.assertEqual(self.getComment(vdata.metadata), 'saved v%s' % counter)
        

class TestMemoryStorage(TestZVCStorageTool):

    def installStorageTool(self):
        tool = MemoryStorage()
        setattr(self.portal, tool.getId(), tool)

if __name__ == '__main__':
    framework()
else:
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestZVCStorageTool))
        suite.addTest(makeSuite(TestMemoryStorage))
        return suite
