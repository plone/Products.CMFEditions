## Script (Python) "revertversion"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=version_id
##title=Revert version
##
from Products.CMFEditions import CMFEditionsMessageFactory as _
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError
from Products.CMFPlone.utils import safe_unicode


RESPONSE = context.REQUEST.RESPONSE
putils = container.plone_utils
pr = container.portal_repository
pr.revert(context, version_id)

obj_type_view_url = context.getTypeInfo().getActionInfo('object/view')['url']
if obj_type_view_url != '/':
    view_url = '%s/%s' % (context.absolute_url(), obj_type_view_url)
else:
    view_url = context.absolute_url()

title = safe_unicode(context.title_or_id())
msg = _(u'${title} has been reverted to revision ${version}.',
        mapping={'title': title,
                 'version': version_id})

if pr.supportsPolicy(context, 'version_on_revert'):
    try:
        commit_msg = context.translate(_(u'Reverted to revision ${version}',
                                       mapping={'version': version_id}))
        pr.save(obj=context, comment=commit_msg)
    except FileTooLargeToVersionError:
        putils.addPortalMessage(
  _(u'The most current revision of the file could not be saved before reverting '
    'because the file is too large.'),
       type='warn'
       )

context.plone_utils.addPortalMessage(msg)

return RESPONSE.redirect(view_url)
