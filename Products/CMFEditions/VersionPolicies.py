# -*- coding: utf-8 -*-
#########################################################################
# Copyright (c) 2004, 2005 Alec Mitchell
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
"""Default Version Policy implementations.

"""

from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IVersionPolicy import IVersionPolicy
from zope.interface import implementer


@implementer(IVersionPolicy)
class VersionPolicy(SimpleItem):
    """A simple class for storing version policy information"""

    security = ClassSecurityInfo()

    def __init__(self, obj_id, title, **kw):
        self.id = obj_id
        self.title = title

    security.declarePublic('Title')
    def Title(self):
        return self.title


class ATVersionOnEditPolicy(VersionPolicy):
    """A policy that implements version creation on edit for AT types,
       requires a custom edit_macros.pt and a controller script called
       update_version_on_edit.  This policy automatically adds and removes
       the controller script from the AT edit controller chain on install."""
    FC_ACTION_LIST = ({'template': 'atct_edit',
                       'status': 'success',
                       'action': 'traverse_to',
                       'expression': 'string:update_version_before_edit',
                       'context':None,
                       'button':None},
                      {'template': 'atct_edit',
                       'status': 'success',
                       'action': 'traverse_to',
                       'expression': 'string:add_reference',
                       'context':None,
                       'button':'form_add'},
                      {'template': 'atct_edit',
                       'status': 'success',
                       'action': 'traverse_to',
                       'expression': 'string:go_back',
                       'context':None,
                       'button':'cancel'},
                      {'template': 'validate_integrity',
                       'status': 'success',
                       'action': 'traverse_to',
                       'expression': 'string:update_version_on_edit',
                       'context':None,
                       'button':None},)

    def setupPolicyHook(self, portal, **kw):
        pass

    def removePolicyHook(self, portal, **kw):
        remove_form_controller_overrides(portal, self.FC_ACTION_LIST)


def remove_form_controller_overrides(portal, actions):
    fc = getToolByName(portal, 'portal_form_controller', None)
    # Fake a request because form controller needs one to delete actions
    fake_req = DummyRequest()
    for i, fc_act in enumerate(fc.listFormActions(1)):
        for action in actions:
            if (action['template'] == fc_act.getObjectId() and
                    action['status'] == fc_act.getStatus() and
                    action['context'] == fc_act.getContextType() and
                    action['button'] == fc_act.getButton() and
                    action['action'] == fc_act.getActionType() and
                    action['expression'] == fc_act.getActionArg()):
                fake_req.form['del_id_%s'%i]=True
                fake_req.form['old_object_id_%s'%i]=action['template'] or ''
                fake_req.form['old_context_type_%s'%i]=action['context'] or ''
                fake_req.form['old_button_%s'%i]=action['button'] or ''
                fake_req.form['old_status_%s'%i]=action['status'] or ''
    # Use the private method because the public one does a redirect
    fc._delFormActions(fc.actions,fake_req)

# Fake request class to satisfy formcontroller removal policy
class DummyRequest(dict):
    form = {}
