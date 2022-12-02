from setuptools import find_packages
from setuptools import setup


with open("README.rst") as myfile:
    long_description = myfile.read() + "\n"
with open("CHANGES.rst") as myfile:
    long_description += myfile.read()
version = "4.0.0"

setup(
    name="Products.CMFEditions",
    version=version,
    description="Versioning for Plone",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="Versioning Plone",
    author="CMFEditions contributers",
    author_email="collective-versioning@lists.sourceforge.net",
    url="https://pypi.org/project/Products.CMFEditions",
    license="GPL",
    packages=find_packages(),
    namespace_packages=["Products"],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            "plone.app.testing",
            "plone.app.textfield",
            "Products.CMFDynamicViewFTI",
            "zope.testing",
        ]
    ),
    install_requires=[
        "setuptools",
        "zope.copy",
        "zope.dottedname",
        "zope.i18nmessageid",
        "plone.base",
        "Products.CMFCore >=2.1",
        "Products.CMFDiffTool",  # dependency in diff template
        "Products.CMFUid",
        "Products.GenericSetup >=1.4.0",
        "Products.ZopeVersionControl",
        "Acquisition",
        "Zope>=5",
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
