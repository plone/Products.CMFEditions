#########################################################################
# Copyright (c) 2004, 2005 Alberto Berti, Gregoire Weber.
# Reflab (Vincenzo Di Somma, Francesco Ciriaci, Riccardo Lemmi)
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
"""
"""

from Acquisition import aq_base

# provoke the warning messages before the first test
from OFS.SimpleItem import SimpleItem
from pickle import dumps
from pickle import HIGHEST_PROTOCOL
from pickle import loads
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IModifier import IAttributeModifier
from Products.CMFEditions.interfaces.IModifier import ICloneModifier
from Products.CMFEditions.interfaces.IModifier import IModifierRegistryQuery
from Products.CMFEditions.interfaces.IModifier import IModifierRegistrySet
from Products.CMFEditions.interfaces.IModifier import ISaveRetrieveModifier
from Products.CMFEditions.tests.base import CMFEditionsBaseTestCase
from zope.interface import implementer
from zope.interface.verify import verifyObject


class Dummy(SimpleItem):
    pass


def deepcopy(obj):
    return loads(dumps(obj, HIGHEST_PROTOCOL))


deepcopy(Dummy())


@implementer(ISaveRetrieveModifier)
class SimpleModifierBase:
    def beforeSaveModifier(self, obj, copy_obj):
        try:
            bsm = getattr(copy_obj, self.beforeSaveModifierAttribute)
            bsm += 1
        except AttributeError:
            bsm = 1
        setattr(copy_obj, self.beforeSaveModifierAttribute, bsm)
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_obj):
        try:
            arm = getattr(repo_obj, self.afterRetrieveModifierAttribute)
            arm += 1
        except AttributeError:
            arm = 1
        setattr(repo_obj, self.afterRetrieveModifierAttribute, arm)
        return [], [], {}


class SimpleModifier1(SimpleModifierBase):
    beforeSaveModifierAttribute = "beforeSave1"
    afterRetrieveModifierAttribute = "afterRetrieve1"


class SimpleModifier2(SimpleModifierBase):
    beforeSaveModifierAttribute = "beforeSave2"
    afterRetrieveModifierAttribute = "afterRetrieve2"


class SimpleModifier3(SimpleModifierBase):
    beforeSaveModifierAttribute = "beforeSave3"
    afterRetrieveModifierAttribute = "afterRetrieve3"


class NonModifier(SimpleItem):
    pass


mlog = []


def dictToString(dict):
    dict_list = []
    keys = [key for key in dict.keys()]
    keys.sort()
    for k in keys:
        dict_list.append(f"{k} = {dict[k]}")
    return ", ".join(dict_list)


@implementer(IAttributeModifier, ICloneModifier, ISaveRetrieveModifier)
class LoggingModifierBase:
    def getReferencedAttributes(self, obj):
        referenced_data = {
            "k1": "v1:" + str(self.__class__.__name__),
            "k2": "v2:" + str(self.__class__.__name__),
        }
        mlog.append(
            "%s.getReferencedAttributes: %s"
            % (self.__class__.__name__, dictToString(referenced_data))
        )
        return referenced_data

    def getOnCloneModifiers(self, obj):
        mlog.append("%s.getOnCloneModifiers" % (self.__class__.__name__))

        def persistent_id(obj):
            return None

        def persistent_load(pid):
            # should never reach this!
            assert False

        return persistent_id, persistent_load, [], [], ""

    def beforeSaveModifier(self, obj, obj_clone):
        mlog.append("%s.beforeSaveModifier" % (self.__class__.__name__))
        return {}, [], []

    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        mlog.append("%s.afterRetrieveModifier" % (self.__class__.__name__))
        return [], [], {}


class LoggingModifier_A(LoggingModifierBase):
    pass


class LoggingModifier_B(LoggingModifierBase):
    pass


class LoggingModifier_C(LoggingModifierBase):
    pass


class LoggingModifier_D(LoggingModifierBase):
    pass


loggingModifiers = (
    LoggingModifier_A(),
    LoggingModifier_B(),
    LoggingModifier_C(),
    LoggingModifier_D(),
)


class TestModifierRegistryTool(CMFEditionsBaseTestCase):
    def setUp(self):
        super().setUp()

        # add an additional user
        self.portal.acl_users.userFolderAddUser("reviewer", "reviewer", ["Manager"], "")
        # add a document
        self.portal.invokeFactory("Document", "doc")

        # just unregister the standard modifiers for the unit tests
        portal_modifier = getToolByName(self.portal, "portal_modifier")
        modifiers = portal_modifier.modules.StandardModifiers.modifiers
        for m in modifiers:
            portal_modifier.unregister(m["id"])

    def test00_interface(self):
        portal_modifier = self.portal.portal_modifier

        # test interface conformance
        # verifyObject(IModifier, portal_modifier)
        verifyObject(IModifierRegistrySet, portal_modifier)
        verifyObject(IModifierRegistryQuery, portal_modifier)

    #        verifyObject(IBulkEditableSubscriberRegistry, portal_modifier)

    def test01_modifiersNotCalled(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))

        portal_modifier.register("1", SimpleModifier1())
        portal_modifier.edit("1", condition="python:True")
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        self.assertRaises(AttributeError, getattr, doc_copy, "beforeSave1")
        self.assertRaises(AttributeError, getattr, doc_copy, "afterRetrieve1")

    def test02_enabledModifierCalled(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))

        portal_modifier.register("1", SimpleModifier1())
        portal_modifier.edit("1", enabled=True, condition="python:True")
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)

        portal_modifier.beforeSaveModifier(doc, doc_copy)
        self.assertEqual(doc_copy.beforeSave1, 2)
        self.assertEqual(doc_copy.afterRetrieve1, 1)

    def test03_unregisteredModifiersNotCalled(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))

        portal_modifier.register("1", SimpleModifier1())
        portal_modifier.edit("1", enabled=True, condition="python:True")
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        self.assertEqual(doc_copy.beforeSave1, 1)
        self.assertRaises(AttributeError, getattr, doc_copy, "afterRetrieve1")
        portal_modifier.unregister("1")
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        self.assertEqual(doc_copy.beforeSave1, 1)
        self.assertRaises(AttributeError, getattr, doc_copy, "afterRetrieve1")

    def test04_conditionEvaluated(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))

        portal_modifier.register("1", SimpleModifier1())
        portal_modifier.edit("1", enabled=True, condition="python:False")
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        self.assertRaises(AttributeError, getattr, doc_copy, "beforeSave1")
        self.assertRaises(AttributeError, getattr, doc_copy, "afterRetrieve1")

    def test05_registerANonModifier(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))

        portal_modifier._setObject("doc", NonModifier())
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        self.assertRaises(AttributeError, getattr, doc_copy, "beforeSave1")
        self.assertRaises(AttributeError, getattr, doc_copy, "afterRetrieve1")

    def test06_modifierAddedToTheCorrectPosition(self):
        portal_modifier = self.portal.portal_modifier
        for id in list(portal_modifier.objectIds()):
            portal_modifier.unregister(id)

        m1 = SimpleModifier1()
        m2 = SimpleModifier2()
        m3 = SimpleModifier3()

        portal_modifier.register("1", m1)
        portal_modifier.register("2", m2)
        portal_modifier.register("3", m3, pos=0)

        modifiers = [m.getModifier() for m in portal_modifier.objectValues()]
        self.assertEqual(modifiers, [m3, m1, m2])

    def test07_unregisterModifer(self):
        portal_modifier = self.portal.portal_modifier
        for id in list(portal_modifier.objectIds()):
            portal_modifier.unregister(id)

        m1 = SimpleModifier1()
        m2 = SimpleModifier2()
        m3 = SimpleModifier3()

        portal_modifier.register("1", m1)
        portal_modifier.register("2", m2)
        portal_modifier.register("3", m3, pos=0)

        portal_modifier.unregister("1")

        modifiers = [m.getModifier() for m in portal_modifier.objectValues()]
        self.assertEqual(modifiers, [m3, m2])

    def test08_getModifiers(self):
        portal_modifier = self.portal.portal_modifier

        m1 = SimpleModifier1()
        m2 = SimpleModifier2()
        m3 = SimpleModifier3()

        portal_modifier.register("1", m1)
        portal_modifier.register("2", m2)
        portal_modifier.register("3", m3, pos=0)

        portal_modifier.unregister("1")

        self.assertEqual(portal_modifier.get("2").getModifier(), m2)
        self.assertEqual(portal_modifier.query("2").getModifier(), m2)
        self.assertRaises(AttributeError, portal_modifier.get, "1")
        self.assertEqual(portal_modifier.query("1", None), None)

    def test09_conditionContextSetUpCorretcly(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))

        # just check if variables got defined
        condition = (
            'python:"%s\n %s\n %s\n %s\n %s\n %s\n %s\n %s\n %s\n %s" % ('
            "object_url, "
            "folder_url, "
            "portal_url, "
            "object, "
            "folder, "
            "portal, "
            "nothing, "
            "request, "
            "modules, "
            "member,"
            ")"
        )
        portal_modifier.register("1", SimpleModifier1())
        portal_modifier.edit("1", enabled=True, condition=condition)

        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        self.assertEqual(doc_copy.beforeSave1, 1)
        self.assertEqual(doc_copy.afterRetrieve1, 1)

    def test10_callingOrder(self):
        global mlog
        portal_modifier = self.portal.portal_modifier
        for id in list(portal_modifier.objectIds()):
            portal_modifier.unregister(id)
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))

        mlog = []
        counter = 0
        for m in loggingModifiers:
            counter += 1
            portal_modifier.register(str(counter), m)
            portal_modifier.edit(str(counter), enabled=True, condition="python:True")

        mlog.append("<save>")
        portal_modifier.getReferencedAttributes(doc)
        portal_modifier.getOnCloneModifiers(doc)
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        mlog.append("<retrieve>")

        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        mlog.append("<end>")

        mlog_str = "\n".join(mlog).replace(
            "__main__", "CMFEditions.tests.test_ModifierRegistryTool"
        )
        expected_result = """<save>
%(class)s_A.getReferencedAttributes: k1 = v1:%(class)s_A, k2 = v2:%(class)s_A
%(class)s_B.getReferencedAttributes: k1 = v1:%(class)s_B, k2 = v2:%(class)s_B
%(class)s_C.getReferencedAttributes: k1 = v1:%(class)s_C, k2 = v2:%(class)s_C
%(class)s_D.getReferencedAttributes: k1 = v1:%(class)s_D, k2 = v2:%(class)s_D
%(class)s_A.getOnCloneModifiers
%(class)s_B.getOnCloneModifiers
%(class)s_C.getOnCloneModifiers
%(class)s_D.getOnCloneModifiers
%(class)s_A.beforeSaveModifier
%(class)s_B.beforeSaveModifier
%(class)s_C.beforeSaveModifier
%(class)s_D.beforeSaveModifier
<retrieve>
%(class)s_D.afterRetrieveModifier
%(class)s_C.afterRetrieveModifier
%(class)s_B.afterRetrieveModifier
%(class)s_A.afterRetrieveModifier
<end>""" % {
            "class": "LoggingModifier"
        }
        self.assertEqual(mlog_str, expected_result)
