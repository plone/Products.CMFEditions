"""
CMFEditions setup handlers.
"""

from Products.CMFCore.utils import getToolByName
from Products.CMFEditions import StandardModifiers

import logging


logger = logging.getLogger(__name__)


def importVarious(context):
    """
    Import various settings.

    Provisional handler that does initialization that is not yet taken
    care of by other handlers.
    """
    # Only run step if a flag file is present
    if context.readDataFile("cmfeditions_various.txt") is None:
        return
    site = context.getSite()
    portal_modifier = getToolByName(site, "portal_modifier", None)
    if portal_modifier is None:
        return
    StandardModifiers.install(portal_modifier)
    portal_repository = getToolByName(site, "portal_repository")
    portal_repository.setAutoApplyMode(True)
    portal_repository._migrateVersionPolicies()


def installSkipRegistryBasesPointersModifier(context):
    """Upgrade step to install the component registry bases modifier."""
    portal_modifier = getToolByName(context, "portal_modifier", None)
    StandardModifiers.install(portal_modifier, ["SkipRegistryBasesPointers"])


def removeBrokenModifiers(context):
    """Remove broken modifiers.

    For Plone 6 we have removed Archetypes support.
    This includes removing classes for four Archetypes modifiers.
    During normal usage you should not notice this.
    But it is still better to remove them.
    """
    from Products.CMFEditions.interfaces.IModifier import IConditionalModifier

    tool = getToolByName(context, "portal_modifier", None)
    for modifier_id, modifier in tool.objectItems():
        if not IConditionalModifier.providedBy(modifier):
            continue
        if not modifier.isBroken():
            continue
        tool._delObject(modifier_id)
        logger.info("Removed broken %s from portal_modifier.", modifier_id)


def removeSkinLayer(context):
    """Remove our skin layer."""
    skins = getToolByName(context, "portal_skins")
    # Remove directory views for directories missing on the filesystem
    our_skin = "CMFEditions"
    if our_skin in skins.keys():
        skins._delObject(our_skin)
        logger.info("Removed %s from skin layers.", our_skin)

    for layer, paths in skins.selections.items():
        paths = paths.split(",")
        if our_skin not in paths:
            continue
        paths.remove(our_skin)
        skins.selections[layer] = ",".join(paths)
        logger.info("Removed %s from skin selection %s.", our_skin, layer)
