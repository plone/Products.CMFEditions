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
action = type_info.getActionById('view')

version_view = getattr(context, action, None)

if hasattr(version_view, 'macros'):
  return version_view.macros['main']
else:
  # XXX This is a misuse of immediate view, also this needs to optionally
  # support the new plone 2.1 default view machanisms.
  version_view = context.restrictedTraverse(context.immediate_view)

  return version_view.macros['main']