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
                      context.getTypeInfo().getActionInfo('object/view')['url']
                     )
msg = u"'%s' has been reverted to version %s" % (context.title_or_id(), version_id)
if pr.supportsPolicy(context, 'version_on_revert'):
    pr.save(obj=context, comment="Reverted to version %s" % version_id)
plone_tool = context.plone_utils
plone_tool.addPortalMessage(msg)
return RESPONSE.redirect(view_url)
