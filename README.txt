===========
CMFEditions
===========

------
README
------

CMFEditions provides versioning in Plone.

- It works out of the box.
- It's higly extensible for specific use cases.

Out Of The Box Experience
=========================

Versionable content items edit views now allows saving a version on save
(automatically or manually). The version history may be accessed quickly from
the view view.

Versionable content types also have an additional tab with version related
functionality:

- save new version
- preview an old version
- retrieve an old version (replacing the current state in the tree)
- diffing versions

A content panel allows configuring the versioning policy by content type:

- enable or disable versioning
- auto-versioning on save
- auto-versioning on retrieve

By default the contents of a folder is versioned independently of the folder.
This may be changed through the ZMI and for specific cases on python level.
Basic support for Archetypes references is built in.

The current strategy is to save everything of the content item (incl. security
information, workflow state, etc.). On retrieve some of these information are
filtered out. This policy may completely be changed depending on specific needs
(see modifiers below). 

Extensibility
=============

CMFEditions was from the beginning developed with extensibility in mind.
A handful of tools provide the whole functionality:

- repository layer: This is the public main API. The repository layer 
  cares about recursive storing and retrieving of content items from/to
  Zope 2's Object File System (OFS).
- archivist layer: It knows *how to clone* content items. The 
  archivist "is Mr. Pickle".
- modifiers: They're invoked by the archivist and know *what to clone*.
  This the main customization point. A modifier knows about what 
  information on an object is a reference and if the referenced object
  has to be versioned also.
- storage: Is responsible of storing content items versions in a 
  history. The current storage implementation is a ZODB storage (it 
  uses Zope Version Control Product from ZC). Other storages may be
  written (svn, file based, xml based, etc.). The storage API is quite
  simple and the storage implementation doesn't have to care about 
  reference stuff as this is already done by the upper layers.
- purge policy: The purge policy is called on every save operations
  and has full control over the version to save and the whole history.
  The current implementation may be configured to only hold the n 
  current versions by purging the older versions from the repository.
  This functionality is by default disabled. It may be enabled through 
  the ZMI. You should take care when you're saving objects with a lot 
  of interrelations. Purging functionality is quite new!


Additional Documentation
========================

A couple of presentations and ReSt documents may be found in 
documentation package that has to be downloaded separately (or the 
``doc`` folder of CMFEditions).

The CMFEditions team also started adding `documentation in the download 
area <http://plone.org/products/cmfeditions/documentation>` of plone.org.
You're welcome to help out.


Dependencies
============

CMFEditions is part of the Plone distribution and all dependencies are already
included. Please refer to the dependency information of Plone for any details.


Migrating from Older Versions of CMFEditions
============================================

We know there are severe problems when migrating from 1.0alpha3, 
1.0alpha4 or trunk checkout from May 2006 and before.
Please `contact us <mailto:collective-versioning@lists.sourceforge.net>` 
for assistance. We're interested in making migrations bullet proof.


Feedback
========

- Please `report bugs <http://plone.org/products/cmfeditions/issues>` 
  to the CMFEditions tracker on plone.org.
- For feedback and questions the developers may be contacted on the 
  `mailing list <mailto:collective-versioning@lists.sourceforge.net>`.


Contributing
============

Just do it and communicate with us over the 
`mailing list <mailto:collective-versioning@lists.sourceforge.net>`!


Credits & Sponsoring
====================

Several people and organizations have made CMFEditions possible:

  See CREDITS.txt
