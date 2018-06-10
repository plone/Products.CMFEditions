from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing.bbb import PloneTestCase
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE

import unittest


class CMFEditionsFixture(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpPloneSite(self, portal):
        # Disable automatic versioning of core content types
        for name in ('Document', 'Event', 'Link', 'News Item'):
            fti = portal.portal_types[name]
            behaviors = list(fti.behaviors)
            behaviors.remove('plone.app.versioningbehavior.behaviors.IVersionable')
            fti.behaviors = tuple(behaviors)


CMFEDITIONS_FIXTURE = CMFEditionsFixture()
CMFEDITIONS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CMFEDITIONS_FIXTURE,),
    name="CMFEditions:Integration",
)


class CMFEditionsBaseTestCase(unittest.TestCase):
    """ A base class for Products.CMFEditions testing """

    layer = CMFEDITIONS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

class CMFEditionsATBaseTestCase(PloneTestCase):
    """A base class for testing CMFEditions with Archetypes"""
