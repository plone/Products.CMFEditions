#########################################################################
# Copyright (c) 2004, 2005 Alberto Berti, Gregoire Weber.
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
$Id: test_ModifierRegistryTool.py,v 1.12 2005/02/25 22:04:00 tomek1024 Exp $
"""

import os, sys
import time

from pickle import dumps, loads, HIGHEST_PROTOCOL

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

try:
    from Interface.Verify import verifyObject
except ImportError:
    # for Zope versions before 2.6.0
    # XXX not sure if 'objectImplements' is correct
    from Interface import objectImplements as verifyObject

from Testing.ZopeTestCase import ZopeTestCase
from Products.CMFTestCase import CMFTestCase

from Acquisition import aq_base
from OFS.ObjectManager import BadRequestException

from Products.CMFCore.utils import getToolByName

from Products.CMFEditions.interfaces.IModifier import IModifierRegistrySet
from Products.CMFEditions.interfaces.IModifier import ISaveRetrieveModifier
from Products.CMFEditions.interfaces.IModifier import IAttributeModifier
from Products.CMFEditions.interfaces.IModifier import ICloneModifier
from Products.CMFEditions.interfaces.IModifier import IModifierRegistryQuery
from Products.CMFEditions.interfaces.IModifier import IBulkEditableModifierRegistry

from Products.CMFEditions.Extensions import Install

# install additional products
CMFTestCase.installProduct('CMFUid')
CMFTestCase.installProduct('CMFEditions')

# Create a CMF site in the test (demo-) storage
CMFTestCase.setupCMFSite()

# provoke the warning messages before the first test
from OFS.SimpleItem import SimpleItem
class Dummy(SimpleItem): 
    pass
def deepcopy(obj):
    return loads(dumps(obj, HIGHEST_PROTOCOL))
deepcopy(Dummy())


class SimpleModifierBase:
  
    __implements__ = (ISaveRetrieveModifier,)
    
    def beforeSaveModifier(self, obj, copy_obj):
        try:
            bsm = getattr(copy_obj, self.beforeSaveModifierAttribute)
            bsm += 1
        except AttributeError:
            bsm = 1
        setattr(copy_obj, self.beforeSaveModifierAttribute, bsm)
        return [], []
            
    def afterRetrieveModifier(self, obj, repo_obj):
        try:
            arm = getattr(repo_obj, self.afterRetrieveModifierAttribute)
            arm += 1
        except AttributeError:
            arm = 1
        setattr(repo_obj, self.afterRetrieveModifierAttribute, arm)

class SimpleModifier1(SimpleModifierBase):
    beforeSaveModifierAttribute = 'beforeSave1'
    afterRetrieveModifierAttribute = 'afterRetrieve1'

class SimpleModifier2(SimpleModifierBase):
    beforeSaveModifierAttribute = 'beforeSave2'
    afterRetrieveModifierAttribute = 'afterRetrieve2'

class SimpleModifier3(SimpleModifierBase):
    beforeSaveModifierAttribute = 'beforeSave3'
    afterRetrieveModifierAttribute = 'afterRetrieve3'

class NonModifier(SimpleItem):
    pass

mlog = []

def dictToString(dict):
    dict_list = []
    keys = [key for key in dict.keys()]
    keys.sort()
    for k in keys:
        dict_list.append("%s = %s" % (k, dict[k]))
    return ', '.join(dict_list)

class LoggingModifierBase:

    __implements__ = (IAttributeModifier, ICloneModifier, ISaveRetrieveModifier)

    def getReferencedAttributes(self, obj):
        referenced_data = {
            'k1': 'v1:'+str(self.__class__), 
            'k2': 'v2:'+str(self.__class__), 
        }
        mlog.append("%s.getReferencedAttributes: %s" % 
                    (self.__class__, dictToString(referenced_data)))
        return referenced_data
        
    def getOnCloneModifiers(self, obj):
        mlog.append("%s.getOnCloneModifiers" % (self.__class__))
        
        def persistent_id(obj):
            return None
            
        def persistent_load(pid):
            # should never reach this!
            assert False
        
        return persistent_id, persistent_load, [], [], ''

    def beforeSaveModifier(self, obj, obj_clone):
        mlog.append("%s.beforeSaveModifier" % (self.__class__))
        return [], []
        
    def afterRetrieveModifier(self, obj, repo_clone, preserve=()):
        mlog.append("%s.afterRetrieveModifier" % (self.__class__))

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

class TestModifierRegistryTool(CMFTestCase.CMFTestCase):

    def afterSetUp(self):
        # we need to have the Manager role to be able to add things
        # to the portal root
        self.setRoles(['Manager',])

        # add an additional user
        self.portal.acl_users.userFolderAddUser('reviewer', 'reviewer',
                                                ['Manager'], '')
        
        # add a document
        self.portal.invokeFactory('Document', 'doc')
        
        # add the Editions Tool (this way we test the 'Install' script!)
        Install.Install(self.portal)
        
        # just unregister the standard modifiers for the unit tests
        portal_modifier = getToolByName(self.portal, 'portal_modifier')
        modifiers = portal_modifier.modules.StandardModifiers.modifiers
        for m in modifiers:
            portal_modifier.unregister(m['id'])

    def test00_interface(self):
        portal_modifier = self.portal.portal_modifier

        # test interface conformance
        #verifyObject(IModifier, portal_modifier)
        verifyObject(IModifierRegistrySet, portal_modifier)
        verifyObject(IModifierRegistryQuery, portal_modifier)
#        verifyObject(IBulkEditableSubscriberRegistry, portal_modifier)

    def test01_modifiersNotCalled(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))
        
        portal_modifier.register('1', SimpleModifier1())
        portal_modifier.edit('1', condition='python:True')
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        self.assertRaises(AttributeError, getattr, doc_copy, 'beforeSave1')
        self.assertRaises(AttributeError, getattr, doc_copy, 'afterRetrieve1')
        
    def test02_enabledModifierCalled(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))
        
        portal_modifier.register('1', SimpleModifier1())
        portal_modifier.edit('1', enabled=True, condition='python:True')
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        self.assertEqual(doc_copy.beforeSave1, 2)
        self.assertEqual(doc_copy.afterRetrieve1, 1)
        
    def test03_unregisteredModifiersNotCalled(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))
        
        portal_modifier.register('1', SimpleModifier1())
        portal_modifier.edit('1', enabled=True, condition='python:True')
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        self.assertEqual(doc_copy.beforeSave1, 1)
        self.assertRaises(AttributeError, getattr, doc_copy, 'afterRetrieve1')
        portal_modifier.unregister('1')
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        self.assertEqual(doc_copy.beforeSave1, 1)
        self.assertRaises(AttributeError, getattr, doc_copy, 'afterRetrieve1')
    
    def test04_conditionEvaluated(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))
        
        portal_modifier.register('1', SimpleModifier1())
        portal_modifier.edit('1', enabled=True, condition='python:False')
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        self.assertRaises(AttributeError, getattr, doc_copy, 'beforeSave1')
        self.assertRaises(AttributeError, getattr, doc_copy, 'afterRetrieve1')
        
    def test05_registerANonModifier(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))
        
        portal_modifier._setObject('doc', NonModifier())
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        self.assertRaises(AttributeError, getattr, doc_copy, 'beforeSave1')
        self.assertRaises(AttributeError, getattr, doc_copy, 'afterRetrieve1')
    
    def test06_modifierAddedToTheCorrectPosition(self):
        portal_modifier = self.portal.portal_modifier
        
        m1 = SimpleModifier1()
        m2 = SimpleModifier2()
        m3 = SimpleModifier3()
        
        portal_modifier.register('1', m1)
        portal_modifier.register('2', m2)
        portal_modifier.register('3', m3, pos=0)
        
        modifiers = [m.getModifier() for m in portal_modifier.objectValues()]
        self.assertEqual(modifiers, [m3, m1, m2])
        
    def test07_unregisterModifer(self):
        portal_modifier = self.portal.portal_modifier
        
        m1 = SimpleModifier1()
        m2 = SimpleModifier2()
        m3 = SimpleModifier3()
        
        portal_modifier.register('1', m1)
        portal_modifier.register('2', m2)
        portal_modifier.register('3', m3, pos=0)
        
        portal_modifier.unregister('1')

        modifiers = [m.getModifier() for m in portal_modifier.objectValues()]
        self.assertEqual(modifiers, [m3, m2])

    def test08_getModifiers(self):
        portal_modifier = self.portal.portal_modifier
        
        m1 = SimpleModifier1()
        m2 = SimpleModifier2()
        m3 = SimpleModifier3()
        
        portal_modifier.register('1', m1)
        portal_modifier.register('2', m2)
        portal_modifier.register('3', m3, pos=0)
        
        portal_modifier.unregister('1')
        
        self.assertEqual(portal_modifier.get('2').getModifier(), m2)
        self.assertEqual(portal_modifier.query('2').getModifier(), m2)
        self.assertRaises(AttributeError, portal_modifier.get, '1')
        self.assertEqual(portal_modifier.query('1', None), None)

    def test09_conditionContextSetUpCorretcly(self):
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))
        
        # just check if variables got defined
        condition = 'python:"%s\n %s\n %s\n %s\n %s\n %s\n %s\n %s\n %s\n %s" % (' \
                    'object_url, ' \
                    'folder_url, ' \
                    'portal_url, ' \
                    'object, ' \
                    'folder, ' \
                    'portal, ' \
                    'nothing, ' \
                    'request, ' \
                    'modules, ' \
                    'member,' \
                    ')'
        portal_modifier.register('1', SimpleModifier1())
        portal_modifier.edit('1', enabled=True, condition=condition)
        
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        self.assertEqual(doc_copy.beforeSave1, 1)
        self.assertEqual(doc_copy.afterRetrieve1, 1)

    def test10_callingOrder(self):
        global mlog
        portal_modifier = self.portal.portal_modifier
        doc = self.portal.doc
        doc_copy = deepcopy(aq_base(doc))
        
        mlog = []
        counter = 0
        for m in loggingModifiers:
            counter += 1
            portal_modifier.register(str(counter), m)
            portal_modifier.edit(str(counter), enabled=True, condition='python:True')
        
        mlog.append('<save>')
        referenced_data = portal_modifier.getReferencedAttributes(doc)
        portal_modifier.getOnCloneModifiers(doc)
        portal_modifier.beforeSaveModifier(doc, doc_copy)
        mlog.append('<retrieve>')
        
        portal_modifier.afterRetrieveModifier(doc, doc_copy)
        mlog.append('<end>')
        
        mlog_str = '\n'.join(mlog).replace('__main__', 'test_ModifierRegistryTool')
        expected_result = \
"""<save>
test_ModifierRegistryTool.LoggingModifier_A.getReferencedAttributes: k1 = v1:test_ModifierRegistryTool.LoggingModifier_A, k2 = v2:test_ModifierRegistryTool.LoggingModifier_A
test_ModifierRegistryTool.LoggingModifier_B.getReferencedAttributes: k1 = v1:test_ModifierRegistryTool.LoggingModifier_B, k2 = v2:test_ModifierRegistryTool.LoggingModifier_B
test_ModifierRegistryTool.LoggingModifier_C.getReferencedAttributes: k1 = v1:test_ModifierRegistryTool.LoggingModifier_C, k2 = v2:test_ModifierRegistryTool.LoggingModifier_C
test_ModifierRegistryTool.LoggingModifier_D.getReferencedAttributes: k1 = v1:test_ModifierRegistryTool.LoggingModifier_D, k2 = v2:test_ModifierRegistryTool.LoggingModifier_D
test_ModifierRegistryTool.LoggingModifier_A.getOnCloneModifiers
test_ModifierRegistryTool.LoggingModifier_B.getOnCloneModifiers
test_ModifierRegistryTool.LoggingModifier_C.getOnCloneModifiers
test_ModifierRegistryTool.LoggingModifier_D.getOnCloneModifiers
test_ModifierRegistryTool.LoggingModifier_A.beforeSaveModifier
test_ModifierRegistryTool.LoggingModifier_B.beforeSaveModifier
test_ModifierRegistryTool.LoggingModifier_C.beforeSaveModifier
test_ModifierRegistryTool.LoggingModifier_D.beforeSaveModifier
<retrieve>
test_ModifierRegistryTool.LoggingModifier_D.afterRetrieveModifier
test_ModifierRegistryTool.LoggingModifier_C.afterRetrieveModifier
test_ModifierRegistryTool.LoggingModifier_B.afterRetrieveModifier
test_ModifierRegistryTool.LoggingModifier_A.afterRetrieveModifier
<end>"""
        self.assertEqual(mlog_str, expected_result)


if __name__ == '__main__':
    framework()
else:
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestModifierRegistryTool))
        return suite
