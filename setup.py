# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '2.2.16'

setup(name='Products.CMFEditions',
      version=version,
      description="Versioning for Plone",
      long_description=open("README.rst").read() + '\n' +
                       open("CHANGES.rst").read(),
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Framework :: Plone :: 5.0',
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
            'plone.app.testing',
        ]
      ),
      install_requires=[
        'setuptools',
        'zope.copy',
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
        'ZODB3>=3.9.0',  # blob support
        'Zope2',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
