# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.DirectoryView import addDirectoryViews

from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes import listTypes
from Products.FAQ import PROJECTNAME,product_globals

from StringIO import StringIO

class PloneSkinRegistrar:
    """
    Controls (un)registering of a layer in the skins tool:
     - the layer in the content of the skin tool
     - the layer in the path of all skins
    @author: U{Gilles Lenfant <glenfant@bigfoot.com>}
    @version: 0.1.0
    @ivar _layer: Name of the Product's subdirectory that contains
        the various layers for the Product.
    @type _layer: string
    @ivar _prodglobals: Globals from this Product.
    @type _propglobals: mapping object
    """

    def __init__(self, skinsdir, prodglobals):
        """Constructor
        @param skinsdir: Name of the Product's subdirectory that
            contains the various layers for the Product.
        @type skinsdir: string
        @param prodglobals: Globals from this Product.

            should be provided by Product's C{__init__.py} like this:

            C{product_globals = globals()}

        @type propglobals: mapping object
        @return: None
        """

        self._skinsdir = skinsdir
        self._prodglobals = prodglobals
        return

    def install(self, aq_obj,position=None,mode='after',layerName=None):
        """Installs and registers the skin resources
        @param aq_obj: object from which cmf site object is acquired
        @type aq_obj: any Zope object in the CMF
        @return: Installation log
        @rtype: string
        """

        rpt = '=> Installing and registering layers from directory %s\n' % self._skinsdir
        skinstool = getToolByName(aq_obj, 'portal_skins')

        # Create the layer in portal_skins

        try:
            if self._skinsdir not in skinstool.objectIds():
                addDirectoryViews(skinstool, self._skinsdir, self._prodglobals)
                rpt += 'Added "%s" directory view to portal_skins\n' % self._skinsdir
            else:
                rpt += 'Warning: directory view "%s" already added to portal_skins\n' % self._skinsdir
        except:
            # ugh, but i am in stress
            rpt += 'Warning: directory view "%s" already added to portal_skins\n' % self._skinsdir


        # Insert the layer in all skins
        # XXX FIXME: Actually assumes only one layer directory with the name of the Product
        # (should be replaced by a smarter solution that finds individual Product's layers)

        if not layerName:
            layerName = self._prodglobals['__name__'].split('.')[-1]

        skins = skinstool.getSkinSelections()

        for skin in skins:
            layers = skinstool.getSkinPath(skin)
            layers = [layer.strip() for layer in layers.split(',')]
            if layerName not in layers:
                try:
                    pos=layers.index(position)
                    if mode=='after': pos=pos+1
                except ValueError:
                    pos=len(layers)

                layers.insert(pos, layerName)

                layers = ','.join(layers)
                skinstool.addSkinSelection(skin, layers)
                rpt += 'Added "%s" to "%s" skin\n' % (layerName, skin)
            else:
                rpt += '! Warning: skipping "%s" skin, "%s" is already set up\n' % (skin, type)
        return rpt
# /class PloneSkinRegistrar

def install(self):
    portal=getToolByName(self,'portal_url').getPortalObject()
    out = StringIO()
    classes=listTypes(PROJECTNAME)
    installTypes(self, out,
                 classes,
                 PROJECTNAME)

    print >> out, "Successfully installed %s." % PROJECTNAME
    sr = PloneSkinRegistrar('skins', product_globals)
    print >> out,sr.install(self)
    print >> out,sr.install(self,position='custom',mode='after',layerName=PROJECTNAME+'_public')

    return out.getvalue()

def uninstall(self):
    out = StringIO()
    classes=listTypes(PROJECTNAME)

    #unregister folderish classes in use_folder_contents
    props=getToolByName(self,'portal_properties').site_properties
    use_folder_tabs=list(props.use_folder_tabs)
    print >> out, 'removing classes from use_folder_tabs:'
    for cl in classes:
        print >> out,  'type:', cl['klass'].portal_type
        if cl['klass'].isPrincipiaFolderish and not cl['klass'].portal_type in []:
            if cl['klass'].portal_type in use_folder_tabs:
                use_folder_tabs.remove(cl['klass'].portal_type)

    props.use_folder_tabs=tuple(use_folder_tabs)

    return out.getvalue()
