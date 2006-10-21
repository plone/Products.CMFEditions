print 'Product FAQ installed'

import os.path

try:
    import CustomizationPolicy
except ImportError:
    CustomizationPolicy=None

from Products.CMFCore import utils, DirectoryView
from Products.Archetypes.atapi import *
from Products.Archetypes import listTypes

##Import Types here to register them (were removed by pyflake check!)
import FAQ
import FAQQuestion

ADD_CONTENT_PERMISSION = '''Add FAQ content'''
PROJECTNAME = "FAQ"

product_globals=globals()

DirectoryView.registerDirectory('skins', product_globals)
DirectoryView.registerDirectory('skins/faq', product_globals)


def initialize(context):
    ##Import Types here to register them

    content_types, constructors, ftis = process_types(
        listTypes(PROJECTNAME),
        PROJECTNAME)

    utils.ContentInit(
        PROJECTNAME + ' Content',
        content_types      = content_types,
        permission         = ADD_CONTENT_PERMISSION,
        extra_constructors = constructors,
        fti                = ftis,
        ).initialize(context)

    if CustomizationPolicy and hasattr(CustomizationPolicy,'register'):
        CustomizationPolicy.register(context)
        print 'Customizationpolicy for FAQ installed'
