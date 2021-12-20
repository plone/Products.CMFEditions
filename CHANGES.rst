Changelog
=========

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

4.0.0a1 (2021-04-26)
--------------------

Breaking changes:


- Removed support for Archetypes, Zope 2 and Python 2.
  Removed Archetypes-only modifiers: ``RetainATRefs``, ``NotRetainATRefs``, ``SkipBlobs``, ``CloneBlobs``.
  Added upgrade step to remove these modifiers from the ``portal_modifier`` tool.
  This is for Plone 6 only.
  [maurits] (#74)
- Update for Plone 6 with Bootstrap markup
  [petschki] (#79)


New features:


- Handle broken VersionPolicies and modifiers in a nicer way.

  - ``ConditionalModifier.isApplicable``: return False when modifier is broken.
  - ``portal_repository.listPolicies``: log and ignore Broken VersionPolicies.

  [maurits] (#74)
- Barceloneta LTS support
  [petschki] (#77)


3.3.4 (2020-04-23)
------------------

Bug fixes:


- Minor packaging updates. (#1)


3.3.3 (2019-08-29)
------------------

Bug fixes:


- Fix DeprecationWarning [jensens] (#71)


3.3.2 (2019-05-04)
------------------

Bug fixes:


- Fix release issue in 3.3.1
  [esteele] (#69)


3.3.1 (2019-05-04)
------------------

Bug fixes:


- Avoid ResourceWarnings.
  [gforcada] (#65)
- Made removing of versioning behaviors less strict (named vs dotted).
  [iham] (#67)


3.3.0 (2018-11-06)
------------------

New features:


- Replaced usages of getObjSize with human_readable_size. (#60)


Bug fixes:


- Fix success() responses in controller actions browser views for AT types
  (#62)


3.2.2 (2018-09-23)
------------------

Bug fixes:

- Fix Unauthorized error due to importing six inside Restricted Python
  `Plone issue 2463 <https://github.com/plone/Products.CMFPlone/issues/2463>`_
  [davilima6]
- Migrate Tests away fro  PloneTestCase
  [pbauer]

- Do not run webdav_history.txt in py3 since it breaks tests (no webdav support in py3).
  [pbauer]

- cleanup: isort/formatting/security decorators
  [jensens]

- InitializeClass was moved to AccessControl.class_init - use it.
  [jensens]

- setDefaultRoles is deprecated.
  addPermission from AccessControl.Permission is instead used.
  [jensens]


3.2.1 (2018-06-18)
------------------

Bug fixes:

- Test against plone.app.contenttypes instead of ATContentTypes.
  [davisagli]


3.2.0 (2018-04-03)
------------------

New features:

- Allow disabling versioning per object.
  `Plone issue 2341 <https://github.com/plone/Products.CMFPlone/issues/2341>`_
  [tomgross]

Bug fixes:

- Make imports Python 3 compatible
  [ale-rt, pbauer]

- Don't depend on ZODB version 3 directly
  [tomgross]

3.1.1 (2018-02-05)
------------------

New features:

- Prepare for Python 2 / 3 compatibility
  [davilima6]


3.1 (2017-03-31)
----------------

New features:

- Use the ``processQueue`` from the merged ``collective.indexing``.  [gforcada]


3.0.1 (2017-02-12)
------------------

Bug fixes:

- Make tests run in Zope 4 (includes some cleanup).
  [pbauer]

- Get rid of CMFFormController scripts
  [tomgross]


3.0 (2016-12-05)
----------------

Breaking changes:

- Purge all old revisions of content about to be removed.
  [tschorr]


For older changes, 2.2.23 and earlier, see ``docs/old-changelog.rst``.
