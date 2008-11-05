## Script (Python) "update_version_on_edit"
##title=Edit Content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##

from Products.CMFPlone.utils import base_hasattr
from Products.CMFEditions import CMFEditionsMessageFactory as _
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError


REQUEST = context.REQUEST
pr = context.portal_repository
putils = context.plone_utils
isVersionable = pr.isVersionable(context)

changed = False
if not base_hasattr(context, 'version_id'):
    changed = True
else:
    changed = not pr.isUpToDate(context, context.version_id)

comment = REQUEST.get('cmfeditions_version_comment',"")
if isVersionable and ((changed and \
                       pr.supportsPolicy(context, 'at_edit_autoversion')) or \
                      REQUEST.get('cmfeditions_save_new_version', None)):
    try:
        context.portal_repository.save(obj=context, comment=comment)
    except FileTooLargeToVersionError:
        putils.addPortalMessage(
       _("Versioning for this file has been disabled because it is too large"),
       type="warn"
       )

return state.set(status='success')
