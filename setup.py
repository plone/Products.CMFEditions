from setuptools import find_packages
from setuptools import setup


with open("README.rst") as myfile:
    long_description = myfile.read() + "\n"
with open("CHANGES.rst") as myfile:
    long_description += myfile.read()
version = "4.0.2.rc1"

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
    author="CMFEditions contributors",
    author_email="collective-versioning@lists.sourceforge.net",
    url="https://pypi.org/project/Products.CMFEditions",
    license="GPL",
    packages=find_packages(),
    namespace_packages=["Products"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    extras_require=dict(
        test=[
            "plone.app.contenttypes",
            "plone.app.robotframework",
            "plone.app.testing",
            "plone.app.textfield",
            "plone.base",
            "plone.testing",
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
        "setuptools",
        "zope.copy",
        "zope.dottedname",
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
