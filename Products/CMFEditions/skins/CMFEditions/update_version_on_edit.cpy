## Script (Python) "update_version_on_edit"
##title=Edit Content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##

REQUEST = context.REQUEST
comment = REQUEST.get('cmfeditions_version_comment',None)
pr = context.portal_repository
policy_support = context.portal_repository.supportsPolicy(context,
                                                        'at_edit_autoversion')
if (comment is not None and pr.isVersionable(context) and 
                        pr.supportsPolicy(context, 'at_edit_autoversion')):
    context.portal_repository.save(obj=context, comment=comment)

return state.set(status='success')