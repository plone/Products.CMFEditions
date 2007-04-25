## Script (Python) "migrateStorage"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Migrate the Storage
##
from Products.CMFCore.utils import getToolByName
storage = getToolByName(context, "portal_historiesstorage")
result = storage.migrateStorage()
if result is None:
    return "no storage migration necessary: nothing done"

return "migrated %s histories and a total of %s versions in in %.2f seconds" \
       % result
