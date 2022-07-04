from plone.app.textfield.value import RichTextValue
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from Products.CMFEditions import PACKAGE_HOME
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase
from plone.base.utils import unrestricted_construct_instance

import os


def read_image(file_path):
    with open(os.path.join(PACKAGE_HOME, file_path), "rb") as image:
        data = image.read()
    return data


class TestPloneContents(CMFEditionsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.membership = self.portal.portal_membership
        self.catalog = self.portal.portal_catalog
        self.workflow = self.portal.portal_workflow
        self.portal_repository = self.portal.portal_repository
        self.portal_archivist = self.portal.portal_archivist
        unrestricted_construct_instance("Folder", self.portal, id="folder")
        self.folder = self.portal.folder

    def getPermissionsOfRole(self, role):
        perms = self.portal.permissionsOfRole(role)
        return [p["name"] for p in perms if p["selected"]]

    def metadata_test_one(self, obj):
        self.assertEqual(obj.Title(), "content")
        self.assertEqual(obj.Subject(), ("content",))
        self.assertEqual(obj.Description(), "content")
        self.assertEqual(obj.Contributors(), ("content",))
        self.assertEqual(obj.Language(), "content")
        self.assertEqual(obj.Rights(), "content")

    def metadata_test_two(self, obj):
        self.assertEqual(obj.Title(), "contentOK")
        self.assertEqual(obj.Subject(), ("contentOK",))
        self.assertEqual(obj.Description(), "contentOK")
        self.assertEqual(obj.Contributors(), ("contentOK",))
        self.assertEqual(obj.Language(), "contentOK")
        self.assertEqual(obj.Rights(), "contentOK")

    def testDocument(self):
        self.folder.invokeFactory("Document", id="doc")
        portal_repository = self.portal_repository
        content = self.folder.doc
        content.text = RichTextValue("text v1", "text/plain", "text/plain")
        content.title = "content"
        content.subject = ["content"]
        content.description = "content"
        content.contributors = ["content"]
        content.language = "content"
        content.rights = "content"
        portal_repository.applyVersionControl(content, comment="save no 1")
        content.text = RichTextValue("text v2", "text/plain", "text/plain")
        content.title = "contentOK"
        content.subject = ["contentOK"]
        content.description = "contentOK"
        content.contributors = ["contentOK"]
        content.language = "contentOK"
        content.rights = "contentOK"
        portal_repository.save(content, comment="save no 2")
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.text.raw, "text v1")
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.text.raw, "text v2")
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.text.raw, "text v1")
        self.metadata_test_one(content)

    def testNewsItem(self):
        self.folder.invokeFactory("News Item", id="news_one")
        portal_repository = self.portal_repository
        content = self.folder.news_one
        content.text = RichTextValue("text v1", "text/plain", "text/plain")
        content.title = "content"
        content.subject = ["content"]
        content.description = "content"
        content.contributors = ["content"]
        content.language = "content"
        content.rights = "content"
        portal_repository.applyVersionControl(content, comment="save no 1")
        content.text = RichTextValue("text v2", "text/plain", "text/plain")
        content.title = "contentOK"
        content.subject = ["contentOK"]
        content.description = "contentOK"
        content.contributors = ["contentOK"]
        content.language = "contentOK"
        content.rights = "contentOK"
        portal_repository.save(content, comment="save no 2")
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.text.raw, "text v1")
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.text.raw, "text v2")
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.text.raw, "text v1")
        self.metadata_test_one(content)

    def testImage(self):
        self.folder.invokeFactory("Image", id="image")
        portal_repository = self.portal_repository
        img1 = read_image("tests/images/img1.png")
        img2 = read_image("tests/images/img2.png")
        content = self.folder.image
        content.image = NamedBlobImage(img1, "img1.png", "image/png")
        content.title = "content"
        content.subject = ["content"]
        content.description = "content"
        content.contributors = ["content"]
        content.language = "content"
        content.rights = "content"
        portal_repository.applyVersionControl(content, comment="save no 1")
        content.image = NamedBlobImage(img2, "img2.png", "image/png")
        content.title = "contentOK"
        content.subject = ["contentOK"]
        content.description = "contentOK"
        content.contributors = ["contentOK"]
        content.language = "contentOK"
        content.rights = "contentOK"
        portal_repository.save(content, comment="save no 2")
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.image.data, img1)
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.image.data, img2)
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.image.data, img1)
        self.metadata_test_one(content)

    def testFile(self):
        self.folder.invokeFactory("File", id="file")
        file1 = read_image("tests/images/img1.png")
        file2 = read_image("tests/images/img2.png")
        portal_repository = self.portal_repository
        content = self.folder.file
        content.file = NamedBlobFile(file1, "img1.png", "image/png")
        content.title = "content"
        content.subject = ["content"]
        content.description = "content"
        content.contributors = ["content"]
        content.language = "content"
        content.rights = "content"
        portal_repository.applyVersionControl(content, comment="save no 1")
        content.file = NamedBlobImage(file2, "img2.png", "image/png")
        content.title = "contentOK"
        content.subject = ["contentOK"]
        content.description = "contentOK"
        content.contributors = ["contentOK"]
        content.language = "contentOK"
        content.rights = "contentOK"
        portal_repository.save(content, comment="save no 2")
        obj = portal_repository.retrieve(content, 0).object
        self.assertEqual(obj.file.data, file1)
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.assertEqual(obj.file.data, file2)
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.assertEqual(content.file.data, file1)
        self.metadata_test_one(content)

    def testFolder(self):
        self.folder.invokeFactory("Image", id="folder")
        portal_repository = self.portal_repository
        content = self.folder.folder
        content.title = "content"
        content.subject = ["content"]
        content.description = "content"
        content.contributors = ["content"]
        content.language = "content"
        content.rights = "content"
        portal_repository.applyVersionControl(content, comment="save no 1")
        content.title = "contentOK"
        content.subject = ["contentOK"]
        content.description = "contentOK"
        content.contributors = ["contentOK"]
        content.language = "contentOK"
        content.rights = "contentOK"
        portal_repository.save(content, comment="save no 2")
        obj = portal_repository.retrieve(content, 0).object
        self.metadata_test_one(obj)
        obj = portal_repository.retrieve(content, 1).object
        self.metadata_test_two(obj)
        portal_repository.revert(content, 0)
        self.metadata_test_one(content)
