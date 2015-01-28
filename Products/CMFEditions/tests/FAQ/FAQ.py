# -*- coding: utf-8 -*-
# File: FAQ.py
"""\
unknown

RCS-ID $Id: FAQ.py,v 1.1 2005/04/20 15:43:37 duncanb Exp $
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

from zope.interface import implements
from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import *
from Products.CMFPlone.interfaces import INonStructuralFolder
from Products.CMFDynamicViewFTI.fti import DynamicViewTypeInformation
from Products.FAQ import PROJECTNAME

##code-section module-header #fill in your manual code here
##/code-section module-header


class FAQ(OrderedBaseFolder):
    security = ClassSecurityInfo()
    portal_type = meta_type = 'FAQ'
    archetype_name = 'FAQ'   #this name appears in the 'add' box
    allowed_content_types = ['FAQQuestion']
    _at_fti_meta_type = DynamicViewTypeInformation.meta_type
    implements(INonStructuralFolder)

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    schema=BaseFolderSchema + Schema((
        TextField('summary',
            widget=TextAreaWidget(description='Enter a value for summary.',
                description_msgid='FAQ_help_summary',
                i18n_domain='FAQ',
                label='Summary',
                label_msgid='FAQ_label_summary',
            ),
        ),

        TextField('introduction',
            widget=TextAreaWidget(description='Enter a value for introduction.',
                description_msgid='FAQ_help_introduction',
                i18n_domain='FAQ',
                label='Introduction',
                label_msgid='FAQ_label_introduction',
            ),
        ),

        LinesField('sections',
            widget=LinesWidget(description='Enter a value for sections.',
                description_msgid='FAQ_help_sections',
                i18n_domain='FAQ',
                label='Sections',
                label_msgid='FAQ_label_sections',
            ),
        ),


        ReferenceField('links',
            allowed_types=(),
            multiValued=1,
            relationship='links',
            versioning=True,
            widget=ReferenceWidget(description='Enter a value for links.',
                description_msgid='FAQ_help_links',
                i18n_domain='FAQ',
                label='Links',
                label_msgid='FAQ_label_links',
            ),
        ),


        ReferenceField('sectionLinks',
            allowed_types=(),
            multiValued=1,
            relationship='sectionLinks',
            widget=ReferenceWidget(description='Enter a value for sectionLinks.',
                description_msgid='FAQ_help_sectionLinks',
                i18n_domain='FAQ',
                label='Sectionlinks',
                label_msgid='FAQ_label_sectionLinks',
            ),
        ),

    ),
    )

    #Methods


    # uncomment lines below when you need
    factory_type_information={
        'allowed_content_types':allowed_content_types,
        'allow_discussion': 0,
        #'content_icon':'FAQ.gif',
        'immediate_view':'base_view',
        'global_allow':1,
        'filter_content_types':1,
        }


    actions=  (


       {'action':      '''string:$object_url/faq_view''',
        'category':    '''object''',
        'id':          'view',
        'name':        'view',
        'permissions': ('''View''',),
        'condition'  : 'python:1'},


          )


registerType(FAQ, PROJECTNAME)
# end of class FAQ

##code-section module-footer #fill in your manual code here
##/code-section module-footer


