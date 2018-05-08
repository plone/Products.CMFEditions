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

from Products.CMFEditions import PACKAGE_HOME
from Products.CMFEditions.tests.base import CMFEditionsATBaseTestCase
import os


class TestATContents(CMFEditionsATBaseTestCase):

    def afterSetUp(self):
        self.membership = self.portal.portal_membership
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow
        self.portal_repository = self.portal.portal_repository

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
        self.folder.invokeFactory('Document', id='doc')
        portal_repository = self.portal_repository
        content = self.folder.doc
        content.setText('têxt v1')
        self.set_metadata(content, 'content')
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.setText('text v2')
        self.set_metadata(content, 'contentOK')
        portal_repository.save(content, comment='save no 2')
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.assertEqual(obj.getRawText(), 'têxt v1')
        self.metadata_test(obj, 'content')
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.assertEqual(obj.getRawText(), 'text v2')
        self.metadata_test(obj, 'contentOK')
        portal_repository.revert(content, 0)
        self.assertEqual(content.getRawText(), 'têxt v1')
        self.metadata_test(content, 'content')

    def testNewsItem(self):
        self.folder.invokeFactory('News Item', id='news_one')
        portal_repository = self.portal_repository
        content = self.folder.news_one
        content.text = 'text v1'
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.text = 'text v2'
        portal_repository.save(content, comment='save no 2')
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.assertEqual(obj.text, 'text v1')
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.assertEqual(obj.text, 'text v2')
        portal_repository.revert(content, 0)
        self.assertEqual(content.text, 'text v1')

    def testImage(self):
        self.folder.invokeFactory('Image', id='image')
        img1 = open(
            os.path.join(PACKAGE_HOME, 'tests/images/img1.png'),
            'rb'
        ).read()
        img2 = open(
            os.path.join(PACKAGE_HOME, 'tests/images/img2.png'),
            'rb'
        ).read()
        portal_repository = self.portal_repository
        content = self.folder.image
        content.edit(image=img1)
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit(image=img2)
        portal_repository.save(content, comment='save no 2')
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.assertEqual(str(obj.getImage()), img1)
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.assertEqual(str(obj.getImage()), img2)
        portal_repository.revert(content, 0)
        self.assertEqual(str(content.getImage()), img1)

    def testFile(self):
        self.folder.invokeFactory('File', id='file')
        file1 = open(
            os.path.join(PACKAGE_HOME, 'tests/file1.dat'),
            'rb'
        ).read()
        file2 = open(
            os.path.join(PACKAGE_HOME, 'tests/file2.dat'),
            'rb'
        ).read()
        portal_repository = self.portal_repository
        content = self.folder.file
        content.edit(file=file1)
        portal_repository.applyVersionControl(content, comment='save no 1')
        content.edit(file=file2)
        portal_repository.save(content, comment='save no 2')
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.assertEqual(str(obj.getFile()), file1)
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.assertEqual(str(obj.getFile()), file2)
        portal_repository.revert(content, 0)
        self.assertEqual(str(content.getFile()), file1)

    def testFolder(self):
        titleOne = 'folderOne'
        titleTwo = 'folderTwo'
        self.folder.invokeFactory('Folder', id='myfolder')
        portal_repository = self.portal_repository
        content = self.folder.myfolder
        content.setTitle(titleOne)
        portal_repository.applyVersionControl(content, comment='save no 0')
        content.setTitle(titleTwo)
        portal_repository.save(content, comment='save no 1')
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.assertEqual(obj.Title(), titleOne)
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.assertEqual(obj.Title(), titleTwo)
        portal_repository.revert(content, 0)
        self.assertEqual(content.Title(), titleOne)

    def testBlobsNotResavedUnlessChanged(self):
        self.folder.invokeFactory('File', id='file')
        file1 = open(
            os.path.join(PACKAGE_HOME, 'tests/images/img1.png'),
            'rb'
        ).read()
        file2 = open(
            os.path.join(PACKAGE_HOME, 'tests/images/img2.png'),
            'rb'
        ).read()
        portal_repository = self.portal_repository
        content = self.folder.file
        content.edit(file=file1)
        original_blob = content.getFile().getBlob()
        portal_repository.applyVersionControl(content, comment='save no 1')
        # Change something that's not the file and resave
        content.edit(title='Title 2')
        portal_repository.save(content, comment='save no 2')
        # Change the file again and resave
        content.edit(file=file2)
        portal_repository.save(content, comment='save no 3')
        # Now let's inspect our versions
        vdata = portal_repository.retrieve(content, 0)
        obj = vdata.object
        self.assertEqual(str(obj.getFile()), file1)
        blob1 = obj.getFile().getBlob()
        # The second version has the same file
        vdata = portal_repository.retrieve(content, 1)
        obj = vdata.object
        self.assertEqual(str(obj.getFile()), file1)
        # Not only is the file the same, the blob is identical, so the
        # data hasn't been copied
        self.assertEqual(obj.getFile().getBlob(), blob1)
        # The blobs we use for versioning are different from the
        # original blob though.  Otherwise we wouldn't have a reliable
        # solution
        self.assertNotEqual(original_blob, blob1)
        # Our third revision has a distinct blob from the current
        # object even though the contents are the same
        vdata = portal_repository.retrieve(content, 2)
        obj = vdata.object
        self.assertEqual(str(obj.getFile()), file2)
        self.assertNotEqual(obj.getFile().getBlob(), content.getFile().getBlob())
        # Reverting gives us the blob saved in versioning, not the original
        portal_repository.revert(content, 0)
        self.assertEqual(content.getFile().getBlob(), blob1)

    def testBlobsNotStringConverted(self):
        file1 = open(os.path.join(PACKAGE_HOME, 'tests/file1.dat')).read()
        content = self.folder[
            self.folder.invokeFactory('File', id='file', file=file1)]

        from Products.CMFCore.utils import getToolByName
        from Products.CMFEditions.interfaces import IArchivist
        archivist = getToolByName(content, 'portal_archivist')

        prepared = archivist.prepare(content)
        for method in ('retrieve', 'isUpToDate', 'save'):
            try:
                getattr(archivist, method)(prepared)
            except IArchivist.ArchivistError as err:
                self.assertFalse(file1 in str(err))
                self.assertFalse(file1 in repr(err))
            else:
                self.fail("Didn't raise ArchivistError")
