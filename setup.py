# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '3.2.2'

setup(
    name='Products.CMFEditions',
    version=version,
    description="Versioning for Plone",
    long_description=(open("README.rst").read() + '\n' +
                      open("CHANGES.rst").read()),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        "License :: OSI Approved :: GNU General Public License (GPL)",
        'Framework :: Plone',
        'Framework :: Plone :: 5.1',
        'Framework :: Zope2',
    ],
    keywords='Versioning Plone',
    author='CMFEditions contributers',
    author_email='collective-versioning@lists.sourceforge.net',
    url='https://pypi.python.org/pypi/Products.CMFEditions',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            'plone.app.testing',
            'plone.app.textfield',
            'Products.CMFPlone',
            'Products.CMFDynamicViewFTI',
            'zope.testing',
        ],
        archetypes=[
            'Products.Archetypes',
        ]
    ),
    install_requires=[
        'setuptools',
        'six',
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
        'Zope2',
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
