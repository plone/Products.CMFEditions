# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import Products.CMFEditions


class ProductsCmfeditionsLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=Products.CMFEditions)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'Products.CMFEditions:CMFEditions')
        for name in ('Document', 'Event', 'Link', 'News Item'):
            fti = portal.portal_types[name]
            behaviors = list(fti.behaviors)
            behaviors.remove('plone.app.versioningbehavior.behaviors.IVersionable')
            fti.behaviors = tuple(behaviors)


PRODUCTS_CMFEDITIONS_FIXTURE = ProductsCmfeditionsLayer()


PRODUCTS_CMFEDITIONS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PRODUCTS_CMFEDITIONS_FIXTURE,),
    name='ProductsCmfeditionsLayer:IntegrationTesting',
)


PRODUCTS_CMFEDITIONS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PRODUCTS_CMFEDITIONS_FIXTURE,),
    name='ProductsCmfeditionsLayer:FunctionalTesting',
)


PRODUCTS_CMFEDITIONS_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PRODUCTS_CMFEDITIONS_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='ProductsCmfeditionsLayer:AcceptanceTesting',
)
