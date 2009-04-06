# -*- coding: utf-8 -*-
"""\
Unit test package for CMFEditions
"""

def installProduct(portal, name, optional=False):
    """Use this to optionaly load products.
    
    Returns True if a product could be installed.
    """
    quickinstaller = portal.portal_quickinstaller
    if optional:
        try:
            quickinstaller.installProduct(name)
        except AttributeError:
            return False
    else:
        quickinstaller.installProduct(name)
    return True
