## Script (Python) "checkUpToDate"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=history
##title=Check if Up To Date
##
from Products.CMFCore.utils import getToolByName
repo = getToolByName(context, "portal_repository", None)

isModified = None
reverted_vid = None
isReverted = None

version_id = getattr(context, "version_id", None)
if repo is not None:
    if version_id is None:
        isModified = True
        isReverted = False
    else:
        isModified = not repo.isUpToDate(context, version_id)
        historyLength = len(history)
        reverted_vid = version_id
        if historyLength == version_id+1:
            isReverted = False
        else:
            isReverted = True
        if isModified:
            version_id = historyLength

return {
    "isModified": isModified,
    "version_id": version_id,
    "isReverted": isReverted,
    "reverted_vid": reverted_vid,
}
