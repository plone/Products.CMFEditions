from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IModifier import IConditionalTalesModifier
from Products.CMFEditions.StandardModifiers import modifiers as standard_modifiers
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import BadRequest
from zope.component import queryMultiAdapter

try:
    from plone.protect import CheckAuthenticator
except ImportError:
    # plone.protect is optional.
    CheckAuthenticator = None

DEFAULT_CONDITIONS = {
    m["id"]: m["condition"] for m in standard_modifiers if "condition" in m
}


class CheckModifierConditions(BrowserView):
    """List the modifiers and compare their TALES condition with the default.

    Allow reverting conditions to their default.
    """

    template = ViewPageTemplateFile("templates/check_modifier_conditions.pt")

    def __call__(self):
        self.messages = []
        form = self.request.form
        if "revert" in form or "revert_all" in form:
            if self.request.method != "POST":
                raise BadRequest("Only POST requests are allowed.")
            if CheckAuthenticator is not None:
                CheckAuthenticator(self.request)
            if "revert_all" in form:
                ids = [info["id"] for info in self.get_modifiers() if info["changed"]]
            else:
                ids = [form.get("modifier_id", "")]
            for modifier_id in ids:
                self.revert(modifier_id)
        return self.template()

    @property
    def tool(self):
        return getToolByName(self.context, "portal_modifier")

    def authenticator(self):
        """Return the hidden _authenticator input, if plone.protect is there."""
        view = queryMultiAdapter((self.context, self.request), name="authenticator")
        if view is None:
            return ""
        return view.authenticator()

    def revert(self, modifier_id):
        default = DEFAULT_CONDITIONS.get(modifier_id)
        modifier = self.tool.query(modifier_id)
        if (
            default is None
            or modifier is None
            or not IConditionalTalesModifier.providedBy(modifier)
        ):
            self.messages.append(f"Cannot revert condition of {modifier_id}.")
            return
        # edit resets 'enabled' and 'title' when they are not passed.
        modifier.edit(
            enabled=modifier.isEnabled(), condition=default, title=modifier.title
        )
        self.messages.append(f"Reverted condition of {modifier_id}.")

    def get_modifiers(self):
        result = []
        for modifier_id, modifier in self.tool.objectItems():
            info = {
                "id": modifier_id,
                "title": getattr(modifier, "title", ""),
                "conditional": False,
                "has_default": False,
                "default": None,
                "condition": None,
                "changed": False,
            }
            if IConditionalTalesModifier.providedBy(modifier):
                default = DEFAULT_CONDITIONS.get(modifier_id)
                condition = modifier.getTalesCondition()
                info["conditional"] = True
                info["has_default"] = default is not None
                info["default"] = default
                info["condition"] = condition
                info["changed"] = default is not None and condition != default
            result.append(info)
        return result
