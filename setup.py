# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '2.2.3'

setup(name='Products.CMFEditions',
      version=version,
      description="Versioning for Plone",
      long_description=open("README.txt").read() + '\n' +
                       open("CHANGES.txt").read(),
      classifiers=[
        'Framework :: Plone',
        'Framework :: Zope2',
      ],
      keywords='Versioning Plone',
      author='CMFEditions contributers',
      author_email='collective-versioning@lists.sourceforge.net',
      url='http://pypi.python.org/pypi/Products.CMFEditions',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(
        test=[
            'zope.testing',
            'Products.CMFPlone',
            'Products.Archetypes',
            'Products.CMFDynamicViewFTI',
            'Products.PloneTestCase',
            'collective.monkeypatcher',  # [test] dependency of plone.app.blob
        ]
      ),
      install_requires=[
        'setuptools',
        'zope.dottedname',
        'zope.i18nmessageid',
        'zope.interface',
        'Products.CMFCore >=2.1',
        'Products.CMFDiffTool',  # dependency in diff template
        'Products.CMFUid',
        'Products.GenericSetup >=1.4.0',
        'Products.ZopeVersionControl',
        'Acquisition',
        'DateTime',
        'transaction',
        'ZODB3',
        'Zope2',
        'plone.app.blob',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
