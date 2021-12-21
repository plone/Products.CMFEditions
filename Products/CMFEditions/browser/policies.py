from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView


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
        self.request.RESPONSE.redirect("versions_history_form")
