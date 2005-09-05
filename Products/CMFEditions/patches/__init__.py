try:
    from Products.Archetypes.CatalogMultiplex import CatalogMultiplex
except ImportError:
    pass
else:
    from Acquisition import aq_base
    
    def __recurseIntoOpaqueItems(self, name, *args):
        """Recurse in opaque items (new in CMF 1.5).
        """
        # This is from CMFCore/CMFCatalogAware.py
        for ob in self.opaqueValues():
            s = getattr(ob, '_p_changed', 0)
            if hasattr(aq_base(ob), name):
                getattr(ob, name)(*args)
            if s is None: ob._p_deactivate()

    CatalogMultiplex_manage_afterAdd = CatalogMultiplex.manage_afterAdd
    def manage_afterAdd(self, item, container):
        """Recurse into opaque items before doing the usual stuff.
        """
        __recurseIntoOpaqueItems(self, 'manage_afterAdd', item, container)
        CatalogMultiplex_manage_afterAdd(self, item, container)
    CatalogMultiplex.manage_afterAdd = manage_afterAdd

    CatalogMultiplex_manage_afterClone = CatalogMultiplex.manage_afterClone
    def manage_afterClone(self, item):
        """Recurse into opaque items before doing the usual stuff.
        """
        __recurseIntoOpaqueItems(self, 'manage_afterClone', item)
        CatalogMultiplex_manage_afterClone(self, item)
    CatalogMultiplex.manage_afterClone = manage_afterClone
    
    CatalogMultiplex_manage_beforeDelete = CatalogMultiplex.manage_beforeDelete
    def manage_beforeDelete(self, item, container):
        """Recurse into opaque items before doing the usual stuff.
        """
        __recurseIntoOpaqueItems(self, 'manage_beforeDelete', item, container)
        CatalogMultiplex_manage_beforeDelete(self, item, container)
    CatalogMultiplex.manage_beforeDelete = manage_beforeDelete

    # just remove all newly added names to not pollute the namespace 
    # of the caller
    del CatalogMultiplex
    del manage_afterAdd
    del manage_afterClone
    del manage_beforeDelete
