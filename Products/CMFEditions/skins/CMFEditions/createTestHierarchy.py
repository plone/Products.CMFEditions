## Script (Python) "createTestHierarchy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Create a test hierarchy for migration tests
##

from Products.CMFCore.utils import getToolByInterfaceName

repo = getToolByInterfaceName('Products.CMFEditions.interfaces.IRepository.IRepositoryTool')
repo.createTestHierarchy(context)
return "finished creating test hierarchy"
