# -*- coding: utf-8 -*-
# File: FAQQuestion.py
"""\
unknown

RCS-ID $Id: FAQQuestion.py,v 1.1 2005/04/20 15:43:37 duncanb Exp $
"""
# Copyright (c) 2005 by unknown
#
# Generated: Wed Apr 20 15:10:54 2005
# Generator: ArchGenXML Version 1.2 devel 3 http://sf.net/projects/archetypes/
#
# GNU General Public Licence (GPL)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#
__author__  = 'unknown <unknown>'
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import *
from Products.CMFDynamicViewFTI.fti import DynamicViewTypeInformation
from Products.FAQ import PROJECTNAME

##code-section module-header #fill in your manual code here
##/code-section module-header


class FAQQuestion(BaseContent):
    security = ClassSecurityInfo()
    portal_type = meta_type = 'FAQQuestion'
    archetype_name = 'Question'   #this name appears in the 'add' box
    allowed_content_types = []
    _at_fti_meta_type = DynamicViewTypeInformation.meta_type

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    schema=BaseSchema + Schema((
        StringField('section',
            widget=StringWidget(description='Enter a value for section.',
                description_msgid='FAQ_help_section',
                i18n_domain='FAQ',
                label='Section',
                label_msgid='FAQ_label_section',
            ),
        ),

        StringField('title',
            widget=StringWidget(description='Enter a value for title.',
                description_msgid='FAQ_help_title',
                i18n_domain='FAQ',
                label='Title',
                label_msgid='FAQ_label_title',
            ),
        ),

        TextField('answer',
            widget=TextAreaWidget(description='Enter a value for answer.',
                description_msgid='FAQ_help_answer',
                i18n_domain='FAQ',
                label='Answer',
                label_msgid='FAQ_label_answer',
            ),
        ),


        ReferenceField('links',
            allowed_types=(),
            multiValued=1,
            relationship='links',
            widget=ReferenceWidget(description='Enter a value for links.',
                description_msgid='FAQ_help_links',
                i18n_domain='FAQ',
                label='Links',
                label_msgid='FAQ_label_links',
            ),
        ),

    ),
    )

    #Methods


    # uncomment lines below when you need
    factory_type_information={
        'allowed_content_types':allowed_content_types,
        'allow_discussion': 0,
        #'content_icon':'FAQQuestion.gif',
        'immediate_view':'base_view',
        'global_allow':0,
        'filter_content_types':1,
        }


    actions=  (


       {'action':      '''string:$object_url/view''',
        'category':    '''object''',
        'id':          'view',
        'name':        'view',
        'permissions': ('''View''',),
        'condition'  : 'python:1'},


          )


registerType(FAQQuestion, PROJECTNAME)
# end of class FAQQuestion

##code-section module-footer #fill in your manual code here
##/code-section module-footer


