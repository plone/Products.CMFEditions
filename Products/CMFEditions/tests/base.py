from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFEditions.testing import PRODUCTS_CMFEDITIONS_INTEGRATION_TESTING

import unittest


class CMFEditionsBaseTestCase(unittest.TestCase):
    """A base class for Products.CMFEditions testing"""

    layer = PRODUCTS_CMFEDITIONS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
