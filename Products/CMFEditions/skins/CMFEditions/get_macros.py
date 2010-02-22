## Script (Python) "get_macros"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##title=
##parameters=vdata

# We need to get the view appropriate for the object in the history, not
# the current object, which may differ due to some migration.
type_info = context.portal_types.getTypeInfo(vdata.object)

# build the name of special versions views
if getattr(type_info, 'getViewMethod', None) is not None:
    # Should use IBrowserDefault.getLayout ?
    def_method_name = type_info.getViewMethod(context)
else:
    def_method_name = type_info.getActionInfo('object/view')['url'].split('/')[-1] or getattr(type_info, 'default_view', 'view')
versionPreviewMethodName = 'version_%s'%def_method_name
versionPreviewTemplate = getattr(context, versionPreviewMethodName, None)

# check if a special version view exists
if getattr(versionPreviewTemplate, 'macros', None) is None:
    # Use the Plone's default view template
    versionPreviewTemplate = context.restrictedTraverse(def_method_name)

if getattr(versionPreviewTemplate, 'macros', None) is None:
    return None

macro_names = ['content-core', 'main']

for name in macro_names:
    if name in versionPreviewTemplate.macros:
        return versionPreviewTemplate.macros[name]
else:
    context.plone_log('(CMFEditions: get_macros.py) Internal error: Missing TAL macros %s in template "%s".' % (', '.join(macro_names), versionPreviewMethodName))
    return None
