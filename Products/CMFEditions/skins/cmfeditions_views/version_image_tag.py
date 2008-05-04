## Script (Python) "version_image_tag"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=here_url, version_id=None
##title=Image tag for specific version
##
obj = context.portal_repository.retrieve(context, version_id).object
working_copy_tag = obj.tag()

# XXX Does someone know a less ugly way to do this?
altPos = working_copy_tag.find("alt=")
tag = '<img src="%s/file_download_version?version_id=%s" %s' % \
      (here_url, version_id, working_copy_tag[altPos:])

return tag
