#########################################################################
# Copyright (c) 2006 Gregoire Weber
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
"""Test the keep the last n version purge policy"""

from .DummyTools import DummyData
from .DummyTools import PurgePolicyTestDummyStorage
from .DummyTools import RemovedData
from Products.CMFEditions.interfaces.IPurgePolicy import IPurgePolicy
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase
from zope.interface.verify import verifyObject


class TestKeepLastNVersionsTool(CMFEditionsBaseTestCase):
    def setUp(self):
        super().setUp()
        # add an additional user
        self.portal.acl_users.userFolderAddUser("reviewer", "reviewer", ["Manager"], "")

        # install test storage
        self._setDummyTool(PurgePolicyTestDummyStorage())

    def _setDummyTool(self, tool):
        setattr(self.portal, tool.getId(), tool)

    def test00_interface(self):
        portal_purgepolicy = self.portal.portal_purgepolicy

        # test interface conformance
        verifyObject(IPurgePolicy, portal_purgepolicy)

    def test01_beforeSaveHookInfinite(self):
        purgepolicy = self.portal.portal_purgepolicy
        storage = self.portal.portal_historiesstorage

        storage.save(history_id=1, obj=DummyData(0))
        res = purgepolicy.beforeSaveHook(history_id=1, obj=2, metadata={})
        self.assertTrue(res)
        self.assertEqual(len(storage.getHistory(history_id=1)), 1)

    def test02_beforeSaveHookKeepsMaximumTwoVersions(self):
        purgepolicy = self.portal.portal_purgepolicy
        storage = self.portal.portal_historiesstorage
        purgepolicy.maxNumberOfVersionsToKeep = 2

        # call hook explicitly before save (dummy tool doesn't call it,
        # we want to do it explicitly)
        res = purgepolicy.beforeSaveHook(history_id=1, obj=2, metadata={})
        self.assertTrue(res)
        storage.save(history_id=1, obj=DummyData(0))
        self.assertEqual(len(storage.getHistory(history_id=1)), 1)

        # call hook explicitly before save (dummy tool doesn't call it,
        # we want to do it explicitly)
        res = purgepolicy.beforeSaveHook(history_id=1, obj=2, metadata={})
        self.assertTrue(res)
        storage.save(history_id=1, obj=DummyData(1))
        self.assertEqual(len(storage.getHistory(history_id=1)), 2)

        # check the first saved version was purged
        res = purgepolicy.beforeSaveHook(history_id=1, obj=2, metadata={})
        self.assertTrue(res)
        storage.save(history_id=1, obj=DummyData(2))
        history = storage.getHistory(history_id=1)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].data, 1)
        self.assertEqual(history[1].data, 2)

    def test03_retrieveOlderSubstitute(self):
        purgepolicy = self.portal.portal_purgepolicy
        storage = self.portal.portal_historiesstorage

        # build history
        storage.save(history_id=1, obj=RemovedData())
        storage.save(history_id=1, obj=DummyData(1))
        storage.save(history_id=1, obj=RemovedData())
        storage.save(history_id=1, obj=RemovedData())
        storage.save(history_id=1, obj=DummyData(4))

        # next newer
        data = purgepolicy.retrieveSubstitute(history_id=1, selector=0)
        self.assertEqual(data.data, 1)
        # next older
        data = purgepolicy.retrieveSubstitute(history_id=1, selector=2)
        self.assertEqual(data.data, 1)
        # next older
        data = purgepolicy.retrieveSubstitute(history_id=1, selector=3)
        self.assertEqual(data.data, 1)
