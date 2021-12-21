from Products.CMFCore.utils import getToolByName
from Products.CMFEditions import CMFEditionsMessageFactory as _
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zope.i18n import translate


class SaveAsNewVersion(BrowserView):
    """Save as new version

    Originally a Script (Python): saveasnewversion
    """

    def __call__(self):
        pr = getToolByName(self.context, "portal_repository", None)
        if pr is not None:
            versioncomment = self.request.get("versioncomment")
            # Note: the save method explicitly checks a permission.
            pr.save(obj=self.context, comment=versioncomment)
        self.request.response.redirect("versions_history_form")


class RevertVersion(BrowserView):
    """Revert version

    Originally a Script (Python): revertversion
    """

    def __call__(self):
        version_id = self.request.get("version_id")
        pr = getToolByName(self.context, "portal_repository")
        pr.revert(self.context, version_id)

        obj_type_view_url = self.context.getTypeInfo().getActionInfo("object/view")[
            "url"
        ]
        if obj_type_view_url != "/":
            view_url = "%s/%s" % (self.context.absolute_url(), obj_type_view_url)
        else:
            view_url = self.context.absolute_url()

        if pr.supportsPolicy(self.context, "version_on_revert"):
            try:
                commit_msg = translate(
                    _(
                        u"Reverted to revision ${version}",
                        mapping={"version": version_id},
                    ),
                    context=self.request,
                )
                pr.save(obj=self.context, comment=commit_msg)
            except FileTooLargeToVersionError:
                IStatusMessage(self.request).addStatusMessage(
                    _(
                        "The most current revision of the file could not be "
                        "saved before reverting because the file is too large."
                    ),
                    "warning",
                )

        title = self.context.title_or_id()
        msg = _(
            "${title} has been reverted to revision ${version}.",
            mapping={"title": title, "version": version_id},
        )
        IStatusMessage(self.request).addStatusMessage(msg, "info")

        return self.request.response.redirect(view_url)
