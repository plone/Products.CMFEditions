## Script (Python) "createTestHierarchy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Create a test hierarchy for migration tests
##
from Products.CMFCore.utils import getToolByName
repo = getToolByName(context, "portal_repository", None)

if repo is not None:
    repo.createTestHierarchy(context)
    return "finished creating test hierarchy"
