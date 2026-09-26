import zope.deferredimport


zope.deferredimport.deprecated(
    "GetMacros has moved to plone.app.layout since Plone 6.3",
    GetMacros="plone.app.layout.cmfeditions.utils:GetMacros",
)
