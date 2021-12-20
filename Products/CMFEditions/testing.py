from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing.zope import WSGI_SERVER_FIXTURE

import Products.CMFEditions


class ProductsCmfeditionsLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=Products.CMFEditions)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "Products.CMFEditions:CMFEditions")
        # with named AND dotted behaviors we need to take care of both
        versioning_behavior = {
            "plone.app.versioningbehavior.behaviors.IVersionable",
            "plone.versioning",
        }
        for name in ("Document", "Event", "Link", "News Item"):
            fti = portal.portal_types[name]
            # write back the behaviors without the versioning behaviors
            # using a Set to keep it simple
            # a = set((1,2,3))
            # b = set([2,4])
            # res = tuple(a.difference(b)) >> (1,3)
            fti.behaviors = tuple(
                set(fti.behaviors).difference(versioning_behavior),
            )


PRODUCTS_CMFEDITIONS_FIXTURE = ProductsCmfeditionsLayer()


PRODUCTS_CMFEDITIONS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PRODUCTS_CMFEDITIONS_FIXTURE,),
    name="ProductsCmfeditionsLayer:IntegrationTesting",
)


PRODUCTS_CMFEDITIONS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PRODUCTS_CMFEDITIONS_FIXTURE,),
    name="ProductsCmfeditionsLayer:FunctionalTesting",
)


PRODUCTS_CMFEDITIONS_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PRODUCTS_CMFEDITIONS_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        WSGI_SERVER_FIXTURE,
    ),
    name="ProductsCmfeditionsLayer:AcceptanceTesting",
)
