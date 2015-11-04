# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from zope.dottedname.resolve import resolve

from Products.CMFEditions.VersionPolicies import VersionPolicy

class RepositoryToolXMLAdapter(XMLAdapterBase):
    """Mode in- and exporter for RepositoryTool.
    """

    name = 'repositorytool'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node=self._doc.createElement('repositorytool')
        node.appendChild(self._extractPolicies())
        node.appendChild(self._extractTypePolicies())
        self._logger.info('RepositoryTool settings exported.')
        return node


    def _importNode(self, node):
        if self.environ.shouldPurge():
            self._purgeTypePolicies()
            self._purgePolicies()
        self._initPolicies(node)
        self._initTypePolicies(node)
        self._logger.info('RepositoryTool settings imported.')

    def _shouldPurge(self, node):
        purge = node.getAttribute('purge').lower() or 'false'
        if purge == 'true':
            return True
        elif purge == 'false':
            return False
        else:
            raise ValueError("purge must be 'true' or 'false'")

    def _purgePolicies(self):
        for policy in self.context.listPolicies():
            self.context.removePolicy(policy.getId())

    def _initPolicies(self, node):
        tool = self.context
        policynames = [p.getId() for p in tool.listPolicies()]
        for child in node.childNodes:
            if child.nodeName == 'policies':
                if self._shouldPurge(child):
                    self._purgePolicies()
                for policy in child.childNodes:
                    if policy.nodeName == '#text':
                        continue
                    assert policy.nodeName == 'policy'
                    policy_id = policy.getAttribute('name')
                    policy_title = policy.getAttribute('title')
                    class_id = policy.getAttribute('class')
                    if class_id:
                        policy_class = resolve(class_id)
                    else:
                        policy_class = VersionPolicy
                    tool.addPolicy(policy_id, policy_title, policy_class)

    def _extractPolicies(self):
        node = self._doc.createElement('policies')
        policies = self.context.listPolicies()
        policies.sort(lambda x, y: cmp(x.getId(), y.getId()))
        for policy in policies:
            p = self._doc.createElement('policy')
            p.setAttribute('name', policy.getId())
            p.setAttribute('title', policy.Title())
            klass = type(policy)
            if klass is not VersionPolicy:
                p.setAttribute('class', "%s.%s" % (klass.__module__, klass.__name__))
            node.appendChild(p)
        return node

    def _purgeTypePolicies(self):
        self.context.manage_setTypePolicies({})
        self.context.setVersionableContentTypes([])

    def _initTypePolicies(self, node):
        tool = self.context
        for child in node.childNodes:
            if child.nodeName == 'policymap':
                if self._shouldPurge(child):
                    self._purgeTypePolicies()
                for p_type in child.childNodes:
                    if p_type.nodeName == '#text':
                        continue
                    assert p_type.nodeName == 'type'
                    portal_type = p_type.getAttribute('name')
                    existing_policies = tool.getPolicyMap().get(portal_type, [])
                    for policy_id in existing_policies:
                        tool.removePolicyFromContentType(portal_type, policy_id)
                    policies = []
                    for policy in p_type.childNodes:
                        if policy.nodeName == '#text':
                            continue
                        assert policy.nodeName == 'policy'
                        policies.append(policy.getAttribute('name'))
                    versionable_types = tool.getVersionableContentTypes()
                    if policies:
                        if portal_type not in versionable_types:
                            versionable_types.append(portal_type)
                        for policy_id in policies:
                            tool.addPolicyForContentType(portal_type, policy_id)
                    else:
                        if portal_type in versionable_types:
                            versionable_types.remove(portal_type)
                    tool.setVersionableContentTypes(versionable_types)


    def _extractTypePolicies(self):
        node = self._doc.createElement('policymap')
        mapping = self.context.getPolicyMap().items()
        mapping.sort()
        for portal_type, policies in mapping:
            t = self._doc.createElement('type')
            t.setAttribute('name', portal_type)
            for policyname in policies:
                p = self._doc.createElement('policy')
                p.setAttribute('name', policyname)
                t.appendChild(p)
            node.appendChild(t)
        return node


def importRepositoryTool(context):
    """Import Repository Tool configuration.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_repository', None)
    if tool is None:
        logger = context.getLogger("repositorytool")
        logger.info("Nothing to import.")
        return

    importObjects(tool, '', context)

def exportRepositoryTool(context):
    """Export Repository Tool configuration.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_repository', None)
    if tool is None:
        logger = context.getLogger("repositorytool")
        logger.info("Nothing to export.")
        return

    exportObjects(tool, '', context)
