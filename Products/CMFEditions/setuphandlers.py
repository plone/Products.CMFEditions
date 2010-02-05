# -*- coding: utf-8 -*-
"""
CMFEditions setup handlers.
"""

from Products.CMFCore.utils import getToolByName
from Products.CMFEditions import StandardModifiers
from Products.CMFEditions.VersionPolicies import ATVersionOnEditPolicy

# File and image versioning are disabled by default until we have modifiers to
# handle their primary fields efficiently
VERSIONING_ACTIONS = {'Document':'version_document_view',
                      #'File':'version_file_view',
                      #'Image':'version_image_view',
                      'News Item':'version_news_item_view',
                      'ATDocument':'version_atdocument_view',
                      'Event': '',
                      'Link': '',
                      #'ATFile':'version_atfile_view',
                      #'ATImage':'version_atimage_view',
                      'ATNewsItem':'version_atnews_item_view',}

ADD_POLICIES = (('at_edit_autoversion',
                    'Create version on edit (AT objects only)',
                     ATVersionOnEditPolicy),
                 ('version_on_revert',
                    'Create version on version revert'),
               )

DEFAULT_POLICIES = ('at_edit_autoversion', 'version_on_revert')


def importVarious(context):
    """
    Import various settings.

    Provisional handler that does initialization that is not yet taken
    care of by other handlers.
    """
    # Only run step if a flag file is present
    if context.readDataFile('cmfeditions_various.txt') is None:
        return
    site = context.getSite()
    portal_modifier = getToolByName(site, 'portal_modifier', None)
    if portal_modifier is None:
        return
    StandardModifiers.install(portal_modifier)
    portal_repository = getToolByName(site, 'portal_repository')
    portal_repository.setAutoApplyMode(True)
    portal_repository.setVersionableContentTypes(VERSIONING_ACTIONS.keys())
    portal_repository._migrateVersionPolicies()
    portal_repository.manage_changePolicyDefs(ADD_POLICIES)
    for ctype in VERSIONING_ACTIONS:
        for policy_id in DEFAULT_POLICIES:
            portal_repository.addPolicyForContentType(ctype, policy_id)
