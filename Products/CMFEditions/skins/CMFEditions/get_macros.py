## Script (Python) "get_macros"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##title=
##parameters=version_id


type_info = context.portal_types.getTypeInfo(context)
action = type_info.getActionById('view') 

version_view = getattr(context, action) 

if hasattr(version_view, 'macros'):
  context.plone_log('ramo if')
  context.plone_log(version_view.macros['main'])

  return version_view.macros['main']
else:
  version_view = context.restrictedTraverse(context.immediate_view)
  context.plone_log('ramo else')
  context.plone_log(version_view.macros['main'])


  return version_view.macros['main']
