# -*- coding: utf-8 -*-
import doctest
import unittest
from plone.app.testing.bbb import PTC_FUNCTIONAL_TESTING
from plone.testing import layered

# These two classes are needed in the doctest. Don't remove it
class DummyFile(object):
    """A sized object"""
    def __init__(self, size):
        self.size = size

    def getSize(self):
        return self.size


class DummyContent(object):
    """An object with annotations"""

    def __init__(self, obid):
        self.id = obid
        self.__annotations__ = {}

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(layered(doctest.DocFileSuite('webdav_history.txt',
                                optionflags=OPTIONFLAGS,
                                package='Products.CMFEditions.tests',),
                          layer=PTC_FUNCTIONAL_TESTING))
    suite.addTest(doctest.DocFileSuite('large_file_modifiers.txt'))
    return suite
