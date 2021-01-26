# -*- coding: utf-8 -*-
import doctest
import unittest


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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocFileSuite('large_file_modifiers.rst'))
    return suite
