## Script (Python) "versioning_config"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=policy_map
##title=versioning config
##

enabled_types = []
type_policies = {}
for p_type in policy_map:
    if p_type.get('enabled', None):
        enabled_types.append(p_type['portal_type'])
    if p_type.get('policies', None):
        type_policies[p_type['portal_type']] = p_type['policies']

context.portal_repository.setVersionableContentTypes(enabled_types)
context.portal_repository.manage_setTypePolicies(type_policies)
context.REQUEST.RESPONSE.redirect(context.absolute_url() + '/versioning_config_form')
