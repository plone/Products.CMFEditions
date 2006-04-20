#########################################################################
# Copyright (c) 2003, 2004, 2005 Alberto Berti, Gregoire Weber,
# Reflab (Vincenzo Di Somma, Francesco Ciriaci, Riccardo Lemmi),
# Duncan Booth
#
# All Rights Reserved.
#
# This file is part of CMFEditions.
#
# CMFEditions is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# CMFEditions is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CMFEditions; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#########################################################################
"""Install script the for EditionsTool in an existing CMF/Plone installation.

Add the following external method to the root of your CMF/Plone instance:

  id:            installEditionsTool
  title:
  Module Name:   CMFEditions.Install
  Function Name: Install

$Id: Install.py,v 1.20 2005/04/01 17:41:55 disommav Exp $
"""
__version__ = "$Revision: 1.20 $"

import os
from OFS.ObjectManager import BadRequestException

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.DirectoryView import addDirectoryViews
from Products.CMFEditions import tools, product_globals
from Products.CMFEditions import StandardModifiers

from Products.CMFEditions.Permissions import ApplyVersionControl
from Products.CMFEditions.Permissions import SaveNewVersion
from Products.CMFEditions.Permissions import AccessPreviousVersions
from Products.CMFEditions.Permissions import CheckoutToLocation
from Products.CMFEditions.Permissions import RevertToPreviousVersions
from Products.CMFEditions.VersionPolicies import ATVersionOnEditPolicy


PROJECTNAME = 'CMFEditions'
SKINS = ('CMFEditions', 'cmfeditions_views')
VERSIONING_ACTIONS = {'Document':'version_document_view',
                      'File':'version_file_view',
                      'Image':'version_image_view',
                      'News Item':'version_news_item_view',
                      'ATDocument':'version_atdocument_view',
                      'ATFile':'version_atfile_view',
                      'ATImage':'version_atimage_view',
                      'ATNewsItem':'version_atnews_item_view',}

DEF_POLICIES = (('at_edit_autoversion',
                    'Create version on edit (AT objects only)',
                     ATVersionOnEditPolicy),
                 ('version_on_rollback',
                    'Create version on version rollback'),   )


def Install(self, tools=tools):
    """Register EditionsTool"""
    portal = getToolByName(self, 'portal_url').getPortalObject()
    out =  []
    write = out.append
    if getToolByName(portal, 'portal_historyidhandler', None) is None:
        if getToolByName(portal, 'portal_uidhandler', None) is None:
            from Products.CMFUid.Extensions import Install as CMFUid_Install
            CMFUid_Install.Install(portal)
        renameTool(portal, 'portal_uidhandler', 'portal_historyidhandler')
    CMFEditions = portal.manage_addProduct['CMFEditions']
    for tool in tools:
        if getToolByName(portal, tool.id, None) is None:
            try:
                CMFEditions.manage_addTool(tool.meta_type)
                write("added '%s' to portal" % tool.id)
            except BadRequestException:
                write("could not add '%s' to portal (possibly because it \
                        already exists)" % tool.id)
    portal_modifier = getToolByName(self, 'portal_modifier')
    StandardModifiers.install(portal_modifier)
    portal_repository = getToolByName(self, 'portal_repository')
    portal_repository.setAutoApplyMode(True)
    portal_repository.setVersionableContentTypes(VERSIONING_ACTIONS.keys())
    portal_repository._migrateVersionPolicies()
    setup_permissions(self, write)
    setup_skins(self, write)
    setup_content_actions(self, write)
    setup_cpanel(self, write)
    add_versioning_policies(self, write)
    #install_customisation(self, write)
    return "\n".join(out)


def renameTool(portal, old_id, new_id):
    """Renames the uid handler to a history id handler.
    """
    tool = getToolByName(portal, old_id)
    # just give it the portals connection if none available
    # XXX check if necessary also for non unit test installs
    saved_jar = tool._p_jar
    if saved_jar is None:
        tool._p_jar = portal._p_jar
    def _setId(new_id):
        tool.id = new_id
    tool._setId = _setId
    portal.manage_renameObjects(ids=[tool.getId()], new_ids=[new_id])
    del tool._setId
    if saved_jar is None:
        tool._p_jar = saved_jar

def setup_permissions(self, write):
    mp = self.manage_permission
    mp(ApplyVersionControl,      ['Owner', 'Reviewer', 'Manager'], 1)
    mp(SaveNewVersion,           ['Owner', 'Reviewer', 'Manager'], 1)
    mp(AccessPreviousVersions,   ['Owner', 'Reviewer', 'Manager'], 1)
    mp(RevertToPreviousVersions, ['Owner', 'Reviewer', 'Manager'], 1)
    mp(CheckoutToLocation,       ['Owner', 'Reviewer', 'Manager'], 1)
    write("setup default permissions")

def setup_skins(self, write):
    st=getToolByName(self, 'portal_skins')
    addDirectoryViews(st, os.path.join('skins'), product_globals)
    for skinname in st.getSkinSelections():
        path=st.getSkinPath(skinname)
        path = [elem.strip() for elem in path.split(',')]
        for fsdv in SKINS:
            if not fsdv in path:
                # Insert after custom so that we can override at skins
                path.insert(1,fsdv)
                write("added folder %r to skin %r" % (fsdv, skinname))
        path=','.join(path)
        st.addSkinSelection(skinname, path)

def setup_content_actions(self, write):
    at = getToolByName(self, 'portal_actions')
    tt = getToolByName(self, 'portal_types')
    vt = getToolByName(self, 'portal_repository')
    if 'Versions' not in [a.getId() for a in vt.listActions()]:
        vt.addAction('Versions',
                     'Versions',
                     'string:${object_url}/versions_history_form',
                     'python:portal.portal_repository.isVersionable(object)',
                     'Modify portal content',
                     'object', )
        write("added versions tab")
    if 'portal_repository' not in at.listActionProviders():
        at.addActionProvider('portal_repository')
    # XXX is this view override stuff really necessary?
#     ftis = tt.listTypeInfo()
#     targets = filter(lambda a : a.getId() in VERSIONING_ACTIONS,
#                      ftis)
#     for fti in targets:
#         url = VERSIONING_ACTIONS[fti.getId()]
#         fti.addAction('version_view',
#                        'version_view',
#                        'string:${object_url}/' + url,
#                        '',
#                        'Modify portal content',
#                        'object',
#                        None)
#         write("added version view for " + fti.content_meta_type)

def setup_cpanel(self, write):
    try:
        portal_conf = getToolByName(self, 'portal_controlpanel')
        id = 'versioning'
        if id not in [ o.id for o in portal_conf.listActions()]:
            portal_conf.registerConfiglet(id
                   , 'Versioning'
                   , 'string:${portal_url}/portal_repository/versioning_config_form'
                   , ''
                   , 'Manage portal'
                   , 'Products'
                   , 1
                   , PROJECTNAME
                   , 'versioning.gif'
                   , 'Versioning Tool'
                   , None
                   )
            write("added versioning tool to Plone control panel")
        else:
            write("versioning tool already on Plone control panel")
    except AttributeError:
        write("no control panel found")

def setup_selenium(self, write):
    # PloneSelenium 
    suites = ['CMFEditions',]
    provider = getToolByName(self, 'portal_selenium')
    if provider:
        for suite in suites:
            # Functional Tests
            action = {'id':suite.lower(),
                      'name':suite,
                      'action':'string:here/get_%s_ftests'%suite.lower(),
                      'condition': '',
                      'permission': 'View',
                      'category':'ftests',
                      'visible': 1}
            provider.addAction(**action)
            write("Action '%s' added to '%s' action provider"
                  % (str(action['id']), 'portal_selenium'))


def add_versioning_policies(self, write):
    pr = getToolByName(self, 'portal_repository', None)
    if pr is not None:
        pr.manage_changePolicyDefs(DEF_POLICIES)


def uninstall(self, tools=tools, reinstall=False):
    id = 'versioning'
    portal = getToolByName(self, 'portal_url').getPortalObject()
    at = getToolByName(portal, 'portal_actions')
    
    #remove policies
    rt = getToolByName(portal, 'portal_repository')
    p_defs = rt._policy_defs
    for policy_id in list(p_defs.keys()):
	    rt.removePolicy(policy_id)
   
    at.deleteActionProvider('portal_repository')
    # rename our uid tool back to the original name if the new tool was
    # removed
    if not reinstall and \
           getToolByName(portal, 'portal_historyidhandler', None) is not None:
        if getToolByName(portal, 'portal_uidhandler', None) is not None:
            portal.manage_delObjects(['portal_uidhandler'])
            renameTool(portal, 'portal_historyidhandler', 'portal_uidhandler')
    # FIX-ME remove also version_view actions from the single FTI
    portal_conf = getToolByName(self, 'portal_controlpanel')
    portal_conf.unregisterConfiglet(id)

def install_customisation(self, write):
    """Default settings may be stored in a customisation policy script so
    that the entire setup may be 'productised'"""

    # Skins are cached during the request so we (in case new skin
    # folders have just been added) we need to force a refresh of the
    # skin.
    self.changeSkin(None)

    scriptname = '%s-customisation-policy' % PROJECTNAME
    cpscript = getattr(self, scriptname, None)

    if cpscript:
        write("Customising %s" % PROJECTNAME)
        write(cpscript())
    else:
        write("No customisation policy")

