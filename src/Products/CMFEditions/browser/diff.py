import zope.deferredimport

zope.deferredimport.deprecated(
    "The history view has moved to plone.app.layout since Plone 6.3",
    DiffView="plone.app.layout.cmfeditions.diff:DiffView",
)
