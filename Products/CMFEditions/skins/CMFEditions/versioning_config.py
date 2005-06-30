## Script (Python) "versioning_config"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=new_content_types
##title=versioning config
##

context.portal_repository.setVersionableContentType(new_content_types)
context.REQUEST.RESPONSE.redirect(context.absolute_url() + '/versioning_config_form')
