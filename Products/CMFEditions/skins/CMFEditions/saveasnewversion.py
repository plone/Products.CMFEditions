## Script (Python) "saveasnewversion"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=versioncomment
##title=Save as new version
##

from Products.CMFCore.utils import getToolByName

pr = getToolByName(context, 'portal_repository', None)
if pr is not None:
    pr.save(obj=context, comment=versioncomment)
    context.REQUEST.RESPONSE.redirect('versions_history_form')
