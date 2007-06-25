## Script (Python) "revertversion"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=version_id
##title=Revert version
##

RESPONSE = context.REQUEST.RESPONSE
pr = container.portal_repository
pr.revert(context, version_id)
view_url = '%s/%s' % (context.absolute_url(),
                      context.getTypeInfo().getActionById('view')
                     )
msg = context.plone_utils.utranslate(msgid="${title} has been reverted to version ${version}", 
                                     domain="cmfeditions",
                                     mapping={'title':context.title_or_id(), 'version':version_id})
if isinstance(msg, unicode):
    msg = msg.encode(context.plone_utils.getSiteEncoding())
if pr.supportsPolicy(context, 'version_on_revert'):
    pr.save(obj=context, comment="Reverted to version %s" % version_id)

return RESPONSE.redirect('%s?portal_status_message=%s' % (view_url, msg))
