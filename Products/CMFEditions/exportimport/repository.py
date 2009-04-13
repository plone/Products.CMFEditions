# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IRepository import IRepositoryTool
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects


class RepositoryToolXMLAdapter(XMLAdapterBase):
    """Mode in- and exporter for RepositoryTool.
    """
    __used_for__ = IRepositoryTool

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node=self._doc.createElement('repositorytool')
        node.appendChild(self._extractPolicies())

        self._logger.info('RepositoryTool settings exported.')
        return node


    def _importNode(self, node):
        if self.environ.shouldPurge():
            self._purgePolicies()

        self._initPolicies(node)
        self._logger.info('RepositoryTool settings imported.')


    def _purgePolicies(self):
        # XXX
        pass


    def _initPolicies(self, node):
        for child in node.childNodes:
            if child.nodeName=='policies':
                # XXX
                pass

    def _extractPolicies(self):
        node=self._doc.createElement('policies')
        # XXX
        return node


def importRepositoryTool(context):
    """Import Repository Tool configuration.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_repository')

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
