from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions import CMFEditionsMessageFactory as _
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError
from Products.CMFEditions.utilities import isObjectChanged
from Products.CMFEditions.utilities import isObjectVersioned
from Products.CMFEditions.utilities import maybeSaveVersion
from Products.statusmessages.interfaces import IStatusMessage

class UpdateVersionOnEditView(BrowserView):

    def success(self):
        return self.context.restrictedTraverse('content_edit')

    def __call__(self):
        context = aq_inner(self.context)
        pf = getToolByName(context, 'portal_factory')

        if pf.isTemporary(context):
            # don't do anything if we're in the factory
            return self.success()

        comment = _("Initial revision")

        if isObjectVersioned(context):
            return self.success()

        try:
            maybeSaveVersion(context, comment=comment, force=False)
        except FileTooLargeToVersionError:
            pass # the on edit save will emit a warning

        return self.success()


class UpdateVersionBeforeEditView(BrowserView):

    def success(self):
        self.request.response.redirect('view')

    def __call__(self):
        context = aq_inner(self.context)
        comment = self.request.get('cmfeditions_version_comment', '')
        force = self.request.get('cmfeditions_save_new_version', None) is not None

        if not (isObjectChanged(context) or force):
            return self.success()

        try:
            maybeSaveVersion(context, comment=comment, force=force)
        except FileTooLargeToVersionError:
            IStatusMessage(self.request).addStatusMessage(
                _('Versioning for this file has been disabled because it is too large'),
                type='warn'
                )
        return self.success()


class FileDownloadVersionView(BrowserView):

    def __call__(self):
        context = aq_inner(self.context)
        version_id = int(self.request.get('version_id', 1))
        RESPONSE = self.request.RESPONSE

        portal_repository = getToolByName(context, 'portal_repository')
        obj = portal_repository.retrieve(context, version_id).object
        RESPONSE.setHeader('Content-Type', obj.getContentType())
        RESPONSE.setHeader('Content-Length', obj.get_size())
        RESPONSE.setHeader('Content-Disposition',
                           'attachment;filename="%s"'%(obj.getFilename()))
        return obj.data


class VersionImageTagView(BrowserView):

    def __call__(self):
        version_id = int(self.request.get('version_id', 1))
        here_url = self.request.get('here_url', '')
        context = aq_inner(self.context)
        portal_repository = getToolByName(context, 'portal_repository')
        obj = portal_repository.retrieve(context, version_id).object
        working_copy_tag = obj.tag()
        altPos = working_copy_tag.find("alt=")
        tag = '<img src="%s/file_download_version?version_id=%s" %s' % \
              (here_url, version_id, working_copy_tag[altPos:])
        return tag
