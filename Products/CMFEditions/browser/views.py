from Acquisition import aq_inner
from plone.base.utils import human_readable_size
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions import CMFEditionsMessageFactory as _
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError
from Products.CMFEditions.utilities import isObjectChanged
from Products.CMFEditions.utilities import isObjectVersioned
from Products.CMFEditions.utilities import maybeSaveVersion
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage

import os
import zope.deferredimport


zope.deferredimport.deprecated(
    "This class is deprecated since Plone 6",
    VersionView="Products.CMFPlone.browser.ploneview:Plone",
)



class UpdateVersionOnEditView(BrowserView):
    def success(self):
        self.request.response.redirect("view")

    def __call__(self):
        context = aq_inner(self.context)
        pf = getToolByName(context, "portal_factory")

        if pf.isTemporary(context):
            # don't do anything if we're in the factory
            return self.success()

        comment = _("Initial revision")

        if isObjectVersioned(context):
            return self.success()

        try:
            maybeSaveVersion(context, comment=comment, force=False)
        except FileTooLargeToVersionError:
            pass  # the on edit save will emit a warning

        return self.success()


class UpdateVersionBeforeEditView(BrowserView):
    def success(self):
        return self.context.restrictedTraverse("content_edit")

    def __call__(self):
        context = aq_inner(self.context)
        comment = self.request.get("cmfeditions_version_comment", "")
        force = self.request.get("cmfeditions_save_new_version", None) is not None

        if not (isObjectChanged(context) or force):
            return self.success()

        try:
            maybeSaveVersion(context, comment=comment, force=force)
        except FileTooLargeToVersionError:
            IStatusMessage(self.request).addStatusMessage(
                _("Versioning for this file has been disabled because it is too large"),
                type="warn",
            )
        return self.success()


class FileDownloadVersionView(BrowserView):
    def __call__(self):
        context = aq_inner(self.context)
        version_id = int(self.request.get("version_id", 1))
        RESPONSE = self.request.RESPONSE

        portal_repository = getToolByName(context, "portal_repository")
        obj = portal_repository.retrieve(context, version_id).object
        RESPONSE.setHeader("Content-Type", obj.getContentType())
        RESPONSE.setHeader("Content-Length", obj.get_size())
        RESPONSE.setHeader(
            "Content-Disposition", 'attachment;filename="%s"' % (obj.getFilename())
        )
        return obj.data


class VersionImageTagView(BrowserView):
    def __call__(self):
        version_id = int(self.request.get("version_id", 1))
        here_url = self.request.get("here_url", "")
        context = aq_inner(self.context)
        portal_repository = getToolByName(context, "portal_repository")
        obj = portal_repository.retrieve(context, version_id).object
        working_copy_tag = obj.tag()
        altPos = working_copy_tag.find("alt=")
        tag = '<img src="{}/file_download_version?version_id={}" {}'.format(
            here_url,
            version_id,
            working_copy_tag[altPos:],
        )
        return tag


class VersionsHistoryForm(BrowserView):
    def checkUpToDate(self, history):
        """Check if Up To Date.

        This used to be a Script (Python): checkUpToDate
        """
        repo = getToolByName(self.context, "portal_repository", None)

        isModified = None
        reverted_vid = None
        isReverted = None

        version_id = getattr(self.context, "version_id", None)
        if repo is not None:
            if version_id is None:
                isModified = True
                isReverted = False
            else:
                isModified = not repo.isUpToDate(self.context, version_id)
                historyLength = len(history)
                reverted_vid = version_id
                if historyLength == version_id + 1:
                    isReverted = False
                else:
                    isReverted = True
                if isModified:
                    version_id = historyLength

        return {
            "isModified": isModified,
            "version_id": version_id,
            "isReverted": isReverted,
            "reverted_vid": reverted_vid,
        }

    def can_diff(self):
        """Return True if content is diffable"""
        context = self.context
        portal_diff = getToolByName(context, "portal_diff", None)
        return (
            portal_diff
            and len(portal_diff.getDiffForPortalType(context.portal_type)) > 0
        )


css_path = os.path.join(os.path.dirname(__file__), "compare.css")
with open(css_path) as myfile:
    COMPARE_CSS = myfile.read()


class CompareCSS(BrowserView):
    """Formerly skins/CMFEditions/compare.css.dtml

    Should be a browser resource, but I don't want to change plone.app.iterate just now.
    That will further complicate an already complex PR.
    """

    def __call__(self):
        return COMPARE_CSS
