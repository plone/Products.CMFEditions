# -*- coding: utf-8 -*-
#########################################################################
# Copyright (c) 2006 Gregoire Weber
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
"""Storage Migration Support

Creating a test hierarchy for migration tests.

"""
import logging
import os.path
import time
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions import PACKAGE_HOME

logger = logging.getLogger('CMFEditions')

def create(context, type, name):
    context.invokeFactory(type, name)
    obj = getattr(context, name)
    editMethods[type](obj, version=0)
    return obj

def edit(obj, version):
    type = obj.getPortalTypeName()
    editMethods[type](obj, version)

def editEvent(context, version=0):
    title = context.Title()
    desc = context.Description()
    eventType = context.Subject()
    location = context.location
    contact = context.contactName
    name = context.getId()
    if not title:
        title = "0: %s event title" % name
        desc = "0: %s event description" % name
        eventType = "Appointment"
        location = "0: %s event location" % name
        contact = "0: %s event contact" % name
    else:
        title = "%s%s" % (version, title[1:])
        desc = "%s%s" % (version, desc[1:])
        location = "%s%s" % (version, location[1:])
        contact = "%s%s" % (version, contact[1:])

    context.update(title=title, description=desc,
                   eventType=eventType, location=location,
                   contactName=contact)

def editFile(context, version=0):
    title = context.Title()
    desc = context.Description()
    file = context.index_html()
    name = context.getId()
    if not title:
        title = "0: %s file title" % name
        desc = "0: %s file description" % name
        file = 100 * ("0: %s file body\n" % name)
    else:
        title = "%s%s" % (version, title[1:])
        desc = "%s%s" % (version, desc[1:])
        file = 100 * ("%s%s" % (version, ": %s file body\n" % name))
    context.update(title=title, description=desc, file=file)

def editFolder(context, version=0):
    title = context.Title()
    desc = context.Description()
    name = context.getId()
    if not title:
        title = "0: %s folder title" % name
        desc = "0: %s folder description" % name
    title = "%s%s" % (version, title[1:])
    desc = "%s%s" % (version, desc[1:])
    context.folder_edit(title=title, description=desc)

def editImage(context, version=0):
    title = context.Title()
    desc = context.Description()
    image = context.index_html()
    name = context.getId()
    if name.endswith(".gif"):
        name = name[:-4]
    filename = "%s_v%s.gif" % (name, version)
    path = os.path.join(PACKAGE_HOME, "tests", "images", filename)
    if not title:
        title = "0: %s image title" % name
        desc = "0: %s image description" % name
        image = open(path).read()
    else:
        title = "%s%s" % (version, title[1:])
        desc = "%s%s" % (version, desc[1:])
        image = open(path).read()
    context.update(title=title, description=desc, image=image)

def editLink(context, version=0):
    title = context.Title()
    desc = context.Description()
    remoteUrl = context.remoteUrl
    name = context.getId()
    if not title:
        title = "0: %s link title" % name
        desc = "0: %s link description" % name
        remoteUrl = "http://www.plone.org/#%s_v0" % name
    else:
        title = "%s%s" % (version, title[1:])
        desc = "%s%s" % (version, desc[1:])
        remoteUrl = "%s%s" % (remoteUrl[:-1], version)
    context.update(title=title, description=desc, remoteUrl=remoteUrl)

def editNewsItem(context, version=0):
    title = context.Title()
    desc = context.Description()
    text = context.getText()
    name = context.getId()
    if not title:
        title = "0: %s news item title" % name
        desc = "0: %s news item description" % name
        text = "0: %s news item body" % name
    else:
        title = "%s%s" % (version, title[1:])
        desc = "%s%s" % (version, desc[1:])
        text = "%s%s" % (version, text[1:])
    context.update(title=title, description=desc, text=text)

def editDocument(context, version=0):
    title = context.Title()
    desc = context.Description()
    text = context.getText()
    name = context.getId()
    if not title:
        title = "0: %s document title" % name
        desc = "0: %s document description" % name
        text = "0: %s document body" % name
    else:
        title = "%s%s" % (version, title[1:])
        desc = "%s%s" % (version, desc[1:])
        text = "%s%s" % (version, text[1:])
    context.update(title=title, description=desc, text=text)


def editTopic(context, version=0):
    pass

editMethods = {
    "Event": editEvent,
    "File": editFile,
    "Folder": editFolder,
    "Image": editImage,
    "Link": editLink,
    "News Item": editNewsItem,
    "Document": editDocument,
    "Topic": editTopic,
}

hierarchy = {
    "events": ("Folder", "Event", 4, 3),
    "files": ("Folder", "File", 4, 3),
    "folders": ("Folder", "Folder", 3, 3),
    "images": ("Folder", "Image", 2, 4, ".gif"),
    "links": ("Folder", "Link", 4, 3),
    "newsitems": ("Folder", "News Item", 4, 3),
    "documents": ("Folder", "Document", 4, 3),
    "topics": ("Folder", "Topic", 0, 0),
}

def createTestHierarchy(context):
    startTime = time.time()
    repo = getToolByName(context, "portal_repository")
    testRoot = create(context,  "Folder", "CMFEditionsTestHierarchy")
    nbrOfObjects = 0
    nbrOfEdits = 0
    nbrOfSaves = 0
    for name, type in hierarchy.items():
        logger.log(logging.INFO, "createTestHierarchy: creating container %s(%s)" \
            % (name, type[0]))
        folder = create(testRoot, type[0], name)
        nbrOfObjects += 1
        logger.log(logging.INFO, "createTestHierarchy: save #0")
        repo.save(folder, comment="save #0")
        nbrOfSaves += 1
        for i in range(type[2]):
            if len(type) == 5:
                ext = type[4]
            else:
                ext = ""

            # create and save
            objName = name[:-1]+str(i+1)+ext
            logger.log(logging.INFO, "createTestHierarchy: creating %s(%s)" \
                % (objName, type[1]))
            obj = create(folder, type[1], objName)
            nbrOfObjects += 1
            logger.log(logging.INFO, "createTestHierarchy: save #0")
            repo.save(obj, comment="save #0")
            nbrOfSaves += 1

            # edit and save a number of times
            for j in range(1, type[3]):
                logger.log(logging.INFO, "createTestHierarchy: editing")
                edit(obj, j)
                nbrOfEdits += 1
                logger.log(logging.INFO, "createTestHierarchy: save #%s" % j)
                repo.save(obj, comment="save #%s" % j)
                nbrOfSaves += 1

                vers = j + i*(type[3]-1)
                logger.log(logging.INFO, "createTestHierarchy: editing parent")
                edit(folder, vers)
                nbrOfEdits += 1
                logger.log(logging.INFO, "createTestHierarchy: save parent #%s" % vers)
                repo.save(folder, comment="save #%s" % vers)
                nbrOfSaves += 1

    totalTime = time.time() - startTime
    logger.log(logging.INFO,
        "createTestHierarchy: created %s objects, edited them %s times and saved %s versions in total in %.1f seconds" \
        % (nbrOfObjects, nbrOfEdits, nbrOfSaves, round(totalTime, 1)))

    return testRoot
