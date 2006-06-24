===========
CMFEditions
===========

------
README
------

CMFEditions adds versioning to Plone.

- It works out of the box with a stock Plone site.
- It's higly extensible for specific use cases.

After a long alpha phase and already working in some productive sites 
this is the first beta release of CMFEditions. For a detailed list of
changes since the 1.0alpha2 have a look at CHNAGES.txt

.. Note::

   Migrating from older versions of CMFEditions: See notes at the end
   of this document!


Out Of The Box Experience
=========================

Versionable content items edit views now allows saving a version 
on save (automaticaly or manualy). The version history may be 
accessed quickly from the view view.

Versionable content types also have an additional tab with 
version related functionality:

- save new version
- preview an old version
- retrieve an old version (replacing the current state in the tree)
- diffing version (if CMFDiffTool is installed)

A content panel allows configuring the versioning poliicy by content 
type:

- enable or disable versioning
- auto-versioning on save

By default the contents of a folder is versioned independently of 
the folder. This may be changed through the ZMI and for specific 
cases on python level. Basic support for Archetypes references is
built in.

The current strategy is to save everything of the content item 
(incl. security information, workflow state, etc.). On retrieve
some of these information are filtered out. This policy may 
completely be changed depending on specific needs (see modifiers 
below). 

This leeds us to the following topic: Extensibility.


Extensibility
=============

CMFEditions from the beginning was developed with extensibility 
in mind. A handfull of tools are providing the whole functionality:

- repository layer: This is the public main API. The repository layer 
  cares about recursive storing and retreiving of content items from/to
  Zope 2's Object File System (OFS).
- archivist layer: It knows *how to clone* content items. The 
  archivist "is Mr. pickle".
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
  This functionality is by default disabled. It may be disabled through 
  the ZMI. You shoudl take care when you're saveing objects with a lot 
  of interrelations. Puriging functionality is quite new!


Additional Documentation
========================

A couple of presentations and ReSt documents may be found in the ``doc``
folder of CMFEditions.

The CMFEditions team also started adding `documentation to the download 
area <http://plone.org/products/cmfeditions/documentation>` of plone.org.

You're welcome to help out


Dependencies
============

It is important to note that CMFEditions requires Zope 2.8.x or higher
and Plone 2.1.2 and higher to be installed.

For details see DEPENDENCIES.txt


Migrating from Older Versions of CMFEditions
============================================

We know there are problems when migrating from 1.0alpha3, 1.0alpha4 
or trunk checkout from May 2006 and before.
Pleas `contact us <mailto:collective-versioning@lists.sourceforge.net>` 
for assitance. We're interested in making migrations bullet proof.


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
