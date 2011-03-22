from zope.deferredimport import deprecated

deprecated("UniqueIdHandlerTool has been removed; "
    "use Products.CMFEditions.historyidhandlertool.HistoryIdHandlerTool or "
    "Products.CMFUid.UniqueIdHandlerTool.UniqueIdHandlerTool",
    UniqueIdHandlerTool=(
        'Products.CMFUid.UniqueIdHandlerTool:UniqueIdHandlerTool'),
    )
