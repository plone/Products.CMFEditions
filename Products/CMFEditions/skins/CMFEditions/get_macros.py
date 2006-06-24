## Script (Python) "get_macros"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##title=
##parameters=vdata
from zLOG import LOG, INFO

# We need to get the view appropriate for the object in the history, not
# the current object, which may differ due to some migration.
type_info = context.portal_types.getTypeInfo(vdata.object)

# build the name of special versions views
versionPreviewMethodName = "version_%s" % type_info.getViewMethod(context)
versionPreviewTemplate = getattr(context, versionPreviewMethodName, None)

# check if a special version view exists
if getattr(versionPreviewTemplate, 'macros', None) is None:
    # use the plones default view template
    # XXX This is a misuse of immediate view, also this needs to optionally
    # support the new plone 2.1 default view machanisms.
    versionPreviewTemplate = context.restrictedTraverse(context.immediate_view)

return versionPreviewTemplate.macros['main']