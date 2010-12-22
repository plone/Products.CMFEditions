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
from Products.CMFEditions.interfaces.IArchivist import ArchivistUnregisteredError
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError

REQUEST = context.REQUEST
if context.portal_factory.isTemporary(context):
    # don't do anything if we're in the factory
    return state.set(status='success')
pr = context.portal_repository
isVersionable = pr.isVersionable(context)
comment = _("Initial revision")

changed = False
if not base_hasattr(context, 'version_id'):
    changed = True
else:
    try:
        changed = not pr.isUpToDate(context, context.version_id)
    except ArchivistUnregisteredError:
        # XXX: The object is not actually registered, but a version is
        # set, perhaps it was imported, or versioning info was
        # inappropriately destroyed
        changed = True
if not changed:
    return state.set(status='success')

if pr.supportsPolicy(context, 'at_edit_autoversion') and isVersionable:
    try:
        context.portal_repository.save(obj=context, comment=comment)
    except FileTooLargeToVersionError:
        pass # the on edit save will emit a warning

return state.set(status='success')
