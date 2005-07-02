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
"""Test the ATContentTypes content

$Id:$
"""

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
ZopeTestCase.installProduct('Zelenium')
ZopeTestCase.installProduct('PloneSelenium')
ZopeTestCase.installProduct('CMFEditions')
ZopeTestCase.installProduct('ATContentTypes')

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
    if not hasattr(aq_base(portal), 'archetype_tool'):
        portal.portal_quickinstaller.installProduct('Archetypes')
    portal.portal_quickinstaller.installProduct('PortalTransforms')
    portal.portal_quickinstaller.installProduct('PloneSelenium')
    portal.portal_quickinstaller.installProduct('CMFEditions')
    if not quiet: ZopeTestCase._print('Adding ATContentTypes ... ')
    portal.portal_quickinstaller.installProduct('ATContentTypes')
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

    def set_metadata(self, obj, text):
        obj.setTitle(text)
        obj.setSubject(text)
        obj.setDescription(text)
        obj.setContributors(text)
        obj.setLanguage(text)
        obj.setRights(text)

    def metadata_test(self, obj, text):
        self.assertEqual(obj.Title(), text)
        self.assertEqual(obj.Subject(), (text,))
        self.assertEqual(obj.Description(), text)
        self.assertEqual(obj.Contributors(), (text,))
        self.assertEqual(obj.Language(), text)
        self.assertEqual(obj.Rights(), text)

    def getPermissionsOfRole(self, role):
        perms = self.portal.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]

    def testATDocument(self):
        self.folder.invokeFactory('ATDocument', id='doc')
        portal_repository = self.portal_repository
        content = self.folder.doc
        content.text = 'text v1'
        self.set_metadata(content, 'content')
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.text = 'text v2'
        self.set_metadata(content, 'contentOK')
        portal_repository.save(content, comment='save no 2')
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.assertEqual(obj.text, 'text v1')
        self.metadata_test(obj, 'content')
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.assertEqual(obj.text, 'text v2')
        self.metadata_test(obj, 'contentOK')
        portal_repository.revert(content, 0)
        self.assertEqual(content.text, 'text v1')
        self.metadata_test(content, 'content')

    def testNewsItem(self):
        self.folder.invokeFactory('ATNewsItem', id='news_one')
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = self.folder.news_one
        content.text = 'text v1'
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.text = 'text v2'
        portal_repository.save(content, comment='save no 2')
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        self.assertEqual(obj.text, 'text v1')
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        self.assertEqual(obj.text, 'text v2')
        portal_repository.revert(content, 0)
        self.assertEqual(content.text, 'text v1')

    def testImage(self):
        self.folder.invokeFactory('ATImage', id='image')
        img1 = open('img1.png', 'rb').read()
        img2 = open('img2.png', 'rb').read()
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = self.folder.image
        content.edit(file=img1)
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit(file=img2)
        portal_repository.save(content, comment='save no 2')
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        self.assertEqual(obj.data, img1)
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        self.assertEqual(obj.data, img2)
        portal_repository.revert(content, 0)
        self.assertEqual(content.data, img1)

    def testFile(self):
        self.folder.invokeFactory('ATFile', id='file')
        file1 = open('img1.png', 'rb').read()
        file2 = open('img2.png', 'rb').read()
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = self.folder.file
        content.edit(file=file1)
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit(file=file2)
        portal_repository.save(content, comment='save no 2')
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        self.assertEqual(obj.data, file1)
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        self.assertEqual(obj.data, file2)
        portal_repository.revert(content, 0)
        self.assertEqual(content.data, file1)

    def testFolder(self):
        self.folder.invokeFactory('ATFolder', id='folder')
        portal_repository = self.portal_repository
        portal_archivist = self.portal_archivist
        content = self.folder.folder
        portal_repository.applyVersionControl(content, comment='save no 1')
        portal_repository.save(content, comment='save no 2')
        vdata = portal_archivist.retrieve(content, 0)
        obj = vdata.data.object
        vdata = portal_archivist.retrieve(content, 1)
        obj = vdata.data.object
        portal_repository.revert(content, 0)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestATContents))
    return suite


if __name__ == '__main__':
    framework()
