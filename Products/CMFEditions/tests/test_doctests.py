# -*- coding: utf-8 -*-
import doctest
import unittest

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
    res = unittest.TestSuite((
        doctest.DocFileSuite('large_file_modifiers.txt'),
        ))
    return res

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
