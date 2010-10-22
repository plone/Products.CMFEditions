# -*- coding: utf-8 -*-
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

from Products.PloneTestCase import PloneTestCase
PloneTestCase.setupPloneSite()

from zope.interface.verify import verifyObject
from OFS.ObjectManager import ObjectManager

from Products.CMFEditions.ArchivistTool import ObjectData
from Products.CMFEditions.interfaces.IStorage import IStorage
from Products.CMFEditions.interfaces.IStorage import IPurgeSupport
from Products.CMFEditions.interfaces.IStorage import StorageUnregisteredError
from Products.CMFEditions.interfaces.IStorage import StorageRetrieveError

from DummyTools import Dummy as Dummy
from DummyTools import DummyPurgePolicy
from DummyTools import MemoryStorage
from DummyTools import notifyModified

class DummyOM(ObjectManager):
    pass

class TestZVCStorageTool(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])

        # add an additional user
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')

        # eventually install another storage
        self.installStorageTool()

        # reset shadow storage in case versions were created during
        # portal setup
        self.portal.portal_historiesstorage._shadowStorage = None

        # delete purge policy if there is one installed
        try:
            del self.portal.portal_purgepolicy
        except AttributeError:
            pass

    def installStorageTool(self):
        # No op: the storage tool is already installed by installProduct
        pass

    def installPurgePolicyTool(self):
        self._setDummyTool(DummyPurgePolicy())

    def _setDummyTool(self, tool):
        setattr(self.portal, tool.getId(), tool)

    def buildMetadata(self, comment):
        return {'sys_metadata': {'comment': comment}}

    def getComment(self, vdata):
        return vdata.metadata["sys_metadata"]["comment"]

    def test00_interface(self):
        portal_storage = self.portal.portal_historiesstorage

        # test interface conformance
        verifyObject(IStorage, portal_storage)
        verifyObject(IPurgeSupport, portal_storage)

    def test01_saveAfterRegisteringDoesNotRaiseException(self):
        portal_storage = self.portal.portal_historiesstorage
        obj = Dummy()

        sel = portal_storage.register(1, ObjectData(obj),
                                      metadata=self.buildMetadata('saved'))
        self.assertEqual(sel, 0)
        sel = portal_storage.save(1, ObjectData(obj),
                                  metadata=self.buildMetadata('saved'))
        self.assertEqual(sel, 1)

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

        # retrieve the state at registration time
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=0)
        self.assertEqual(retrieved_obj.object.object.text, 'v1 of text')
        self.assertEqual(self.getComment(retrieved_obj), 'saved v1')

        # just check if first save wasn't a double save
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=1)
        self.assertEqual(retrieved_obj.object.object.text, 'v2 of text')
        self.assertEqual(self.getComment(retrieved_obj), 'saved v2')

    def test05_getHistory(self):
        portal_storage = self.portal.portal_historiesstorage

        obj1 = Dummy()
        obj1.text = 'v1 of text'
        portal_storage.register(1, ObjectData(obj1),
                                metadata=self.buildMetadata('saved v1'))

        obj2 = Dummy()
        obj2.text = 'v2 of text'
        portal_storage.save(1, ObjectData(obj2),
                            metadata=self.buildMetadata('saved v2'))

        obj3 = Dummy()
        obj3.text = 'v3 of text'
        portal_storage.save(1, ObjectData(obj3),
                            metadata=self.buildMetadata('saved v3'))

        history = portal_storage.getHistory(history_id=1)
        length = len(history)

        # check length
        self.assertEquals(length, 3)

        # iterating over the history
        for i, vdata in enumerate(history):
            expected_test = 'v%s of text' % (i+1)
            self.assertEquals(vdata.object.object.text, expected_test)
            self.assertEquals(history[i].object.object.text, expected_test)

            expected_comment = 'saved v%s' % (i+1)
            self.assertEqual(self.getComment(vdata), expected_comment)
            self.assertEqual(self.getComment(history[i]), expected_comment)

        # accessing the versions
        self.assertEquals(history[0].object.object.text, "v1 of text")
        self.assertEqual(self.getComment(history[0]), "saved v1")
        self.assertEquals(history[1].object.object.text, "v2 of text")
        self.assertEqual(self.getComment(history[1]), "saved v2")
        self.assertEquals(history[2].object.object.text, "v3 of text")
        self.assertEqual(self.getComment(history[2]), "saved v3")

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

    def _setupMinimalHistory(self):
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

        obj4 = Dummy()
        obj4.text = 'v4 of text'
        portal_storage.save(1, ObjectData(obj4), metadata=self.buildMetadata('saved v4'))

    def test08_lengthAfterHavingPurgedAVersion(self):
        self._setupMinimalHistory()
        portal_storage = self.portal.portal_historiesstorage

        # purge a version
        portal_storage.purge(1, 1, metadata=self.buildMetadata("purged v2"))

        # check length
        lenWith = len(portal_storage.getHistory(1, countPurged=True))
        self.assertEqual(lenWith, 4)
        lenWithout = len(portal_storage.getHistory(1, countPurged=False))
        self.assertEqual(lenWithout, 3)

        # purge again the same version (should not change the purge count)
        portal_storage.purge(1, 1, metadata=self.buildMetadata("purged v2"))

        # check again getLength (unchanged behaviour)
        lenWith = len(portal_storage.getHistory(1, countPurged=True))
        self.assertEqual(lenWith, 4)
        lenWithout = len(portal_storage.getHistory(1, countPurged=False))
        self.assertEqual(lenWithout, 3)

    def test09_retrievePurgedVersionsNoPolicyInstalled(self):
        self._setupMinimalHistory()
        portal_storage = self.portal.portal_historiesstorage

        # purge a version
        portal_storage.purge(1, 2, metadata=self.buildMetadata("purged v3"))

        # ``retrieve`` returns the removed info because there is no purge
        # policy installed
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=2)
        self.failIf(retrieved_obj.isValid())
        self.assertEqual(retrieved_obj.object.reason, "purged")
        self.assertEqual(self.getComment(retrieved_obj), "purged v3")

        retrieved_obj = portal_storage.retrieve(history_id=1, selector=2,
                                                substitute=False)
        self.failIf(retrieved_obj.isValid())
        self.assertEqual(retrieved_obj.object.reason, "purged")
        self.assertEqual(self.getComment(retrieved_obj), "purged v3")

        retrieved_obj = portal_storage.retrieve(history_id=1, selector=2,
                                                countPurged=False)
        self.failUnless(retrieved_obj.isValid())
        self.assertEqual(retrieved_obj.object.object.text, 'v4 of text')
        self.assertEqual(self.getComment(retrieved_obj), 'saved v4')

    def test10_retrievePurgedVersionsWithPolicyInstalled(self):
        self._setupMinimalHistory()
        portal_storage = self.portal.portal_historiesstorage

        # install the purge policy that returns the next older not removed
        self.installPurgePolicyTool()

        # purge
        portal_storage.purge(1, 1, metadata=self.buildMetadata("purged v2"))
        lenAll = len(portal_storage.getHistory(1))
        lenEff = len(portal_storage.getHistory(1, countPurged=False))
        self.assertEqual(lenAll, 4)
        self.assertEqual(lenEff, 3)

        # purge
        portal_storage.purge(1, 2, metadata=self.buildMetadata("purged v3"))
        lenAll = len(portal_storage.getHistory(1))
        lenEff = len(portal_storage.getHistory(1, countPurged=False))
        self.assertEqual(lenAll, 4)
        self.assertEqual(lenEff, 2)

        # ``retrieve`` returns the next older object
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=1)
        self.failUnless(retrieved_obj.isValid())
        self.assertEqual(retrieved_obj.object.object.text, 'v1 of text')
        self.assertEqual(self.getComment(retrieved_obj), 'saved v1')

        retrieved_obj = portal_storage.retrieve(history_id=1, selector=2)
        self.failUnless(retrieved_obj.isValid())
        self.assertEqual(retrieved_obj.object.object.text, 'v1 of text')
        self.assertEqual(self.getComment(retrieved_obj), 'saved v1')

        # ``retrieve`` returns existing object
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=3)
        self.failUnless(retrieved_obj.isValid())
        self.assertEqual(retrieved_obj.object.object.text, 'v4 of text')
        self.assertEqual(self.getComment(retrieved_obj), 'saved v4')

        # check with substitute=False: should return the removed info
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=1,
                                                substitute=False)
        self.failIf(retrieved_obj.isValid())
        self.assertEqual(retrieved_obj.object.reason, "purged")
        self.assertEqual(self.getComment(retrieved_obj), "purged v2")
        retrieved_obj = portal_storage.retrieve(history_id=1, selector=2,
                                                substitute=False)
        self.failIf(retrieved_obj.isValid())
        self.assertEqual(retrieved_obj.object.reason, "purged")
        self.assertEqual(self.getComment(retrieved_obj), "purged v3")

    def test11_purgeOnSave(self):
        # install the purge policy that removes all except the current and
        # previous objects
        self.installPurgePolicyTool()
        portal_storage = self.portal.portal_historiesstorage

        # save no 1
        obj1 = Dummy()
        obj1.text = 'v1 of text'

        sel = portal_storage.register(1, ObjectData(obj1),
                                      metadata=self.buildMetadata('saved v1'))
        history = portal_storage.getHistory(1, countPurged=False)

        self.assertEquals(sel, 0)
        self.assertEquals(len(history), 1)
        self.assertEqual(history[0].object.object.text, 'v1 of text')
        self.assertEqual(self.getComment(history[0]), 'saved v1')

        # save no 2
        obj2 = Dummy()
        obj2.text = 'v2 of text'
        sel = portal_storage.save(1, ObjectData(obj2),
                                  metadata=self.buildMetadata('saved v2'))
        history = portal_storage.getHistory(1, countPurged=False)

        self.assertEquals(sel, 1)
        self.assertEquals(len(history), 2)
        self.assertEqual(history[0].object.object.text, 'v1 of text')
        self.assertEqual(self.getComment(history[0]), 'saved v1')
        self.assertEqual(history[1].object.object.text, 'v2 of text')
        self.assertEqual(self.getComment(history[1]), 'saved v2')

        # save no 3: purged oldest version
        obj3 = Dummy()
        obj3.text = 'v3 of text'
        sel = portal_storage.save(1, ObjectData(obj3),
                                  metadata=self.buildMetadata('saved v3'))
        history = portal_storage.getHistory(1, countPurged=False)
        length = len(history)

        # iterating over the history
        for i, vdata in enumerate(history):
            self.assertEquals(vdata.object.object.text,
                              'v%s of text' % (i+2))
            self.assertEqual(self.getComment(vdata),
                             'saved v%s' % (i+2))

        self.assertEquals(sel, 2)
        self.assertEquals(length, 2)
        self.assertEqual(history[0].object.object.text, 'v2 of text')
        self.assertEqual(self.getComment(history[0]), 'saved v2')
        self.assertEqual(history[1].object.object.text, 'v3 of text')
        self.assertEqual(self.getComment(history[1]), 'saved v3')

        # save no 4: purged oldest version
        obj4 = Dummy()
        obj4.text = 'v4 of text'
        sel = portal_storage.save(1, ObjectData(obj4),
                                  metadata=self.buildMetadata('saved v4'))
        history = portal_storage.getHistory(1, countPurged=False)
        length = len(history)

        # iterating over the history
        for i, vdata in enumerate(history):
            self.assertEquals(vdata.object.object.text,
                              'v%s of text' % (i+3))
            self.assertEqual(self.getComment(vdata),
                             'saved v%s' % (i+3))

        self.assertEquals(sel, 3)
        self.assertEquals(length, 2)
        self.assertEqual(history[0].object.object.text, 'v3 of text')
        self.assertEqual(self.getComment(history[0]), 'saved v3')
        self.assertEqual(history[1].object.object.text, 'v4 of text')
        self.assertEqual(self.getComment(history[1]), 'saved v4')

    def test12_retrieveNonExistentVersion(self):
        portal_storage = self.portal.portal_historiesstorage

        obj1 = Dummy()
        obj1.text = 'v1 of text'
        portal_storage.register(1, ObjectData(obj1), metadata=self.buildMetadata('saved v1'))

        obj2 = Dummy()
        obj2.text = 'v2 of text'
        portal_storage.save(1, ObjectData(obj2), metadata=self.buildMetadata('saved v2'))

        # purge
        portal_storage.purge(1, 0, metadata=self.buildMetadata("purged v1"))

        # retrieve non existing version
        self.assertRaises(StorageRetrieveError,
                          portal_storage.retrieve, history_id=1, selector=2,
                          countPurged=True, substitute=True)

        self.assertRaises(StorageRetrieveError,
                          portal_storage.retrieve, history_id=1, selector=1,
                          countPurged=False)

    def test13_saveWithUnicodeComment(self):
        portal_storage = self.portal.portal_historiesstorage
        obj1 = Dummy()
        obj1.text = 'v1 of text'
        portal_storage.register(1, ObjectData(obj1),
                                metadata=self.buildMetadata('saved v1'))
        portal_storage.save(1, ObjectData(obj1),
                            metadata=self.buildMetadata(u'saved v1\xc3\xa1'))

    def test14_getHistoryMetadata(self):
        portal_storage = self.portal.portal_historiesstorage
        self._setupMinimalHistory()
        history = portal_storage.getHistoryMetadata(1)
        self.assertEqual(len(history), 4)

        # accessing the versions
        self.assertEqual(history.retrieve(0)['metadata']['sys_metadata']['comment'], "saved v1")
        self.assertEqual(history.retrieve(1)['metadata']['sys_metadata']['comment'], "saved v2")
        self.assertEqual(history.retrieve(2)['metadata']['sys_metadata']['comment'], "saved v3")
        self.assertEqual(history.retrieve(3)['metadata']['sys_metadata']['comment'], "saved v4")


class TestMemoryStorage(TestZVCStorageTool):

    def installStorageTool(self):
        # install the memory storage
        tool = MemoryStorage()
        setattr(self.portal, tool.getId(), tool)

from unittest import TestSuite, makeSuite
def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestZVCStorageTool))
    suite.addTest(makeSuite(TestMemoryStorage))
    return suite
