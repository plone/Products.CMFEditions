from pathlib import Path
from setuptools import setup


version = "5.0.0a1"

long_description = (
    f"{Path('README.rst').read_text()}\n{Path('CHANGES.rst').read_text()}"
)

setup(
    name="Products.CMFEditions",
    version=version,
    description="Versioning for Plone",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # Get more strings from
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.2",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="Versioning Plone",
    author="CMFEditions contributors",
    author_email="collective-versioning@lists.sourceforge.net",
    url="https://pypi.org/project/Products.CMFEditions",
    license="GPL",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    extras_require=dict(
        test=[
            "plone.app.contenttypes[test]",
            "plone.app.testing",
            "plone.app.textfield",
            "plone.base",
            "plone.namedfile",
        ]
    ),
    install_requires=[
        "BTrees",
        "Missing",
        "Persistence",
        "Products.CMFCore >=2.1",
        "Products.CMFDiffTool",  # dependency in diff template
        "Products.CMFUid",
        "Products.GenericSetup >=1.4.0",
        "Products.ZopeVersionControl",
        "Products.statusmessages",
        "Zope>=5",
        "plone.folder",
        "plone.locking",
        "zope.copy",
        "zope.dottedname",
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
