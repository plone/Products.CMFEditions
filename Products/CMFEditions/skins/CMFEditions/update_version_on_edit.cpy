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
pr = context.portal_repository
isVersionable = pr.isVersionable(context)
comment = REQUEST.get('cmfeditions_version_comment',"")
if REQUEST.get('cmfeditions_save_new_version',None) and isVersionable:
#     policy_support = context.portal_repository.supportsPolicy(context,
#                                                             'at_edit_autoversion')
#
    context.portal_repository.save(obj=context, comment=comment)

elif comment is not None and pr.supportsPolicy(context, 'at_edit_autoversion') and isVersionable:
    context.portal_repository.save(obj=context, comment=comment)

return state.set(status='success')