from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions import CMFEditionsMessageFactory as _
from Products.Five.browser import BrowserView
from zope.i18n import translate


class DiffView(BrowserView):
    """Compute the diff between two versions of an object.

    This base view holds the API-level logic only, without a template, so
    it stays available to API consumers (plone.restapi, plone.api) that do
    not have plone.app.layout installed. plone.app.layout registers an
    override on IPloneAppLayoutLayer that renders the actual HTML.
    """

    template = None

    def __init__(self, *args):
        super().__init__(*args)
        self.repo_tool = getToolByName(self.context, "portal_repository")

    def getVersion(self, version):
        context = aq_inner(self.context)
        if version == "current":
            return context
        else:
            return self.repo_tool.retrieve(context, int(version)).object

    def versionName(self, version):
        """
        Translate the version name. This is needed to allow translation when `version`
        is the string 'current'.
        """
        return _(version)

    def versionTitle(self, version):
        version_name = self.versionName(version)

        return translate(
            _("version ${version}", mapping=dict(version=version_name)),
            context=self.request,
        )

    def __call__(self):
        version1 = self.request.get("one", "current")
        version2 = self.request.get("two", "current")

        history_metadata = self.repo_tool.getHistoryMetadata(self.context)
        retrieve = history_metadata.retrieve
        getId = history_metadata.getVersionId
        history = self.history = []
        # Count backwards from most recent to least recent
        for i in range(history_metadata.getLength(countPurged=False) - 1, -1, -1):
            version = retrieve(i, countPurged=False)["metadata"].copy()
            version["version_id"] = getId(i, countPurged=False)
            history.append(version)
        dt = getToolByName(self.context, "portal_diff")
        self.changeset = dt.createChangeSet(
            self.getVersion(version2),
            self.getVersion(version1),
            id1=self.versionTitle(version2),
            id2=self.versionTitle(version1),
        )
        self.changes = [
            change for change in self.changeset.getDiffs() if not change.same
        ]

        if self.template is None:
            raise ValueError(
                "You are using the base DiffView view in Products.CMFEditions,"
                " for classic UI, override the DiffView from plone.app.layout"
                " by registering it for your BrowserLayer of"
                " plone.app.layout.interfaces.IPloneAppLayoutLayer."
            )
        return self.template()
