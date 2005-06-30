## Script (Python) "rollbackversion"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=version_id
##title=Rollback version
##

RESPONSE = context.REQUEST.RESPONSE
container.portal_repository.revert(context, version_id)
view_url = '%s/%s' % (context.absolute_url(),
                      context.getTypeInfo().getActionById('view')
                     )
msg = 'portal_status_message=\'%s\' has been rolled back to version %s' % (context.title_or_id(), version_id)
return RESPONSE.redirect('%s?%s' % (view_url, msg))
