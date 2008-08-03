## Script (Python) "saveasnewversion"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=versioncomment
##title=Save as new version
##

container.portal_repository.save(obj=context, comment=versioncomment)
context.REQUEST.RESPONSE.redirect('versions_history_form')