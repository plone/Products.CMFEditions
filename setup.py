from setuptools import setup, find_packages

version = '1.2.7'

setup(name='Products.CMFEditions',
      version=version,
      description="Versioning for Plone",
      long_description=open("README.txt").read() + '\n' +
                       open("CHANGES.txt").read(),
      classifiers=[
        'Framework :: Plone',
      ],
      keywords='Versioning Plone',
      author='CMFEditions contributers',
      author_email='collective-versioning@lists.sourceforge.net',
      url='http://plone.org/products/cmfeditions',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'Products.Archetypes',
        'Products.CMFCore >=2.1',
        'Products.CMFDynamicViewFTI',
        'Plone',
        'Products.CMFUid',
        'Products.GenericSetup >=1.4.0',
        'Products.PloneTestCase',
        'Products.ZopeVersionControl',
        'zope.interface',
      ],
      )
