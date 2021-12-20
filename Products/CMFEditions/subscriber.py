#########################################################################
# Copyright (c) 2008 Alberto Berti, Gregoire Weber.
# All Rights Reserved.
#
# This file is part of CMFEditions.
#
# CMFEditions is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# CMFEditions is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CMFEditions; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#########################################################################
"""Event Subscribers
"""
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IStorage import StorageRetrieveError
from Products.CMFEditions.utilities import dereference


def object_removed(obj, event):
    """an object is being deleted -
    also delete it's history
    """
    if not IContentish.providedBy(obj):
        return
    try:
        histories_storage = getToolByName(obj, "portal_historiesstorage")
        repo_tool = getToolByName(obj, "portal_repository")
    except AttributeError:
        # XXX If tools are missing, there is nothing we can do.
        # This occurs in some Products.CMFDiffTool and
        # Products.CMFTestCase tests for 4.3.x. Maybe it should
        # be fixed there.
        return
    obj, histid = dereference(obj)
    if histid is None:
        return
    metadata = repo_tool.getHistoryMetadata(obj)
    try:
        num_versions = metadata.getLength(countPurged=False)
    except AttributeError:
        # portal_historiesstorage will return
        # an empty list in certain cases,
        # do nothing
        return
    current = metadata.retrieve(num_versions - 1)
    sys_metadata = current["metadata"]["sys_metadata"]
    if ("parent" in sys_metadata) and (sys_metadata["parent"]["history_id"] != histid):
        try:
            histories_storage.retrieve(history_id=sys_metadata["parent"]["history_id"])
            return
        except StorageRetrieveError:
            pass
    length = len(histories_storage.getHistory(histid, countPurged=False))
    for i in range(length):
        histories_storage.purge(
            histid,
            0,
            metadata={"sys_metadata": {"comment": "purged"}},
            countPurged=False,
        )
