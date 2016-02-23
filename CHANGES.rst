Changelog
=========

2.2.20 (unreleased)
-------------------

New:

- *add item here*

Fixes:

- Fixed blob modifiers for dexterity content types
  [Gagaro]


2.2.19 (2016-02-14)
-------------------

Fixes:

- Fixed sometimes failing test.  [maurits]


2.2.18 (2015-11-25)
-------------------

Fixes:

- Removed executable bit from various files.  And do a quick release,
  as on a test server the previous release was somehow missing a file.
  [maurits]


2.2.17 (2015-11-25)
-------------------

Fixes:

- Made storage statistics test more robust.
  See https://github.com/plone/Products.CMFEditions/issues/31
  [tschorr]


2.2.16 (2015-09-27)
-------------------

- Input sanitation for retrieveSubstitute()
  [zupo]


2.2.15 (2015-09-15)
-------------------

- use unrestricted search for storage statistics
  [tschorr]


2.2.14 (2015-08-13)
-------------------

- Do not call ndiff unless there is no html_diff.  Removed strange
  unicode space from template.  Related to
  https://github.com/plone/Products.CMFPlone/issues/820
  [maurits]


2.2.13 (2015-04-26)
-------------------

- Drop use of python:exists() in templates.
  [pbauer]

- Replace deprecated JavaScript functions with their jQuery equivalents.
  [thet]


2.2.12 (2015-03-13)
-------------------

- Remove dependency on old Archetypes tests
  [tomgross]

- Ported tests to plone.app.testing
  [tomgross]

- Removed old FAQ testing code. Should go in a seperate product, if needed.
  [tomgross]

- Frosted cleanups
  [tomgross]

2.2.11 (2014-10-23)
-------------------

- Depend on ZODB3>=3.9.0 for blob support.
  [tomgross]

- Fix AT tests to work with plone.app.blob plone.app.blob >=1.5.11
  [jensens]


2.2.10 (2014-09-07)
-------------------

- Fix #16: Allow developers to define a ``@@version-view`` to customize how a version of an item is
  displayed in ``versions_history_form.pt``.
  [rafaelbco]

- Fix #14: Duplicate functionality in ``@@history`` and ``version_diff.pt``.
  Now ``version_diff.pt`` is deprecated.
  [rafaelbco]

- Fix bug: ``CopyModifyMergeRepositoryTool.manage_setTypePolicies`` method
  modifies sequence while iterating over it.
  [rafaelbco]

- Purging old versions did not properly remove all references
  to the blob fields, resulting in old blobs to stay there forever.
  [do3cc]

2.2.9 (2013-12-07)
------------------

- Use search_icon.png instead of search_icon.gif in version_image_view.pt.
  The page crashed because search_icon.gif couldn't be found.
  [vincentfretin]

- Do not depend on the ``jq`` variable in the history view.
  [maurits]

2.2.8 (2013-03-05)
------------------

- Fix modifier check that made AT assumptions about Dexterity
  content.
  [rpatterson]

- Remove hard dependency on Archetypes.
  [davisagli]

2.2.7 (2013-01-01)
------------------

- put back the history legend for compare/diff versions, fixes #9371
  [maartenkling]

- Site administrators do revisioning

2.2.6 (2012-10-16)
------------------

- Update ``IPossibleSite`` import to ``zope.component``.
  [elro]

2.2.5 (2012-08-11)
------------------

- Fixed version file preview for empty files.
  [thomasdesvenain]

- Fixed versions history form:
  title and description aren't displayed two times.
  [thomasdesvenain]

- Fixed version file preview:
  some displayed values of a previous version were values of current version.
  [thomasdesvenain]

- ArchivistTool.py, DummyTools.py, IArchivist.py, ModifierRegistryTool.py:
  Don't use list as default parameter value.
  [kleist]


2.2.4 (2012-06-27)
------------------

- Add upgrade step to install the component registry bases modifier.
  [rossp]

- Skip blob files from plone.namedfile even when they no longer
  extend the classes from z3c.blobfile.
  [davisagli]

- Declare missing dependency on zope.copy.
  [hannosch]


2.2.3 (2012-01-26)
------------------

- Changed the get_macros python skin script into a browser view.  This
  avoids an Unauthorized exception when viewing revisions when using
  five.pt (Chameleon).
  [maurits]

- Implement a special base modifier that allows retention of specific
  annotation elements from the working copy.  Use this in the OM
  modifiers to ensure we don't stomp annotations for folders on retrieval.
  [alecm]

- If an object has a component registry (AKA site manager), make sure
  the bases of that registry are not recursively copied when saving
  versions.
  [rossp]

2.2.2 (2011-10-17)
------------------

- Don't string convert blobs.  Fixes MemoryErrors or excessive memory
  consumption with large blobs.
  [rossp]

- Protect against anonymous access to KwAsAttributes.
  [mj]

2.2.1 (2011-09-19)
------------------

- Merged changes from 2.1.5.
  [lentinj]

2.2 (2011-08-23)
----------------

- Make Zope 2 permissions available as Zope 3-style permissions.
  [rafaelbco]

- Changed ``@@history`` to be protected by ``CMFEditions.AccessPreviousVersions`` instead of
  ``cmf.ModifyPortalContent``.
  [rafaelbco]

- Only show the "Revert to this version" button if the user has the ``Revert to previous versions``
  permission in ``versions_history_form``.
  [rafaelbco]

2.1.5 (2011-09-19)
------------------

- Translate the commit message, so version id is substituted.
  [lentinj]

- Only save an initial version before edit when content is not yet versioned,
  rather than every time there are unsaved changes. Otherwise there is an
  "Initial version" generated for every edit after publish/retract, as these
  change the publishing date without a new version being saved. Possibly a
  version should be saved on publish, but not sure the extra versioning noise
  is useful.
  [lentinj]

2.1.4 (2011-08-31)
------------------

- Remove references to blobs when cloning blob fields. They are handled as
  referenced attributes anyway. This eliminates the creation of an additional
  empty blob when cloning blob fields.
  [buchi]

- No longer store references in the ZVC wrapper. They are stored in the shadow
  history and retrieved from there. This eliminates the creation of an
  additional empty blob when cloning blob fields.
  [buchi]

- Allow to translate the string "current" in the diff view (``@@history``) and in the
  ``version_diff`` template.
  [rafaelbco]

2.1.3 (2011-04-03)
------------------

- Fixed: Unauthorized error on versions history form for non managers.
  [thomasdesvenain]

2.1.2 (2011-03-25)
------------------

- remove UniqueIdHandlerTool, it was not used anymore;
  nobody (including vds and hannosch) seems to remember what it was for.
  [gotcha]

- fix portal_historyidhandler class to avoid issue where GenericSetup toolset
  import step tried to change the class default id
  [gotcha]

- Skip z3c.blobfile File (notable subclasess plone.namedfile BlobFile and
  BlobImage) as blobfile versioning is not there yet.
  [elro]

2.1.1 - 2011-02-25
------------------

- Fix bug when loading GenericSetup profile with ``<policymap purge="true">``.
  [elro]

2.1.0 - 2011-02-25
------------------

- Generic Setup export/import support.
  [elro]

2.0.5 - 2011-02-25
------------------

- Workaround some potential issues with event handlers and
  transaction.savepoint which can cause exceptions when, for example,
  zope.sendmail is used to send mail in the same transaction as saving
  an edition.
  [rossp]

2.0.4 - 2011-01-03
------------------

- Depend on ``Products.CMFPlone`` instead of ``Plone``.
  [elro]

- Do not provide "Compare to ... revision" link in versions history actions
  if content type has no diffable field.
  [thomasdesvenain]

- Add Site Administrator role to various permissions, for forward compatibility
  with Plone 4.1.
  [davisagli]

2.0.3 - 2010-11-06
------------------

- Internationalized default version comments ('Initial revision', etc.).
  [thomasdesvenain]

- Fixed: version comment was not considered when saving a content with
  automatic version policy. Closes http://dev.plone.org/plone/ticket/8535.
  [thomasdesvenain]

- Fixed multiple chameleon incompatibilities.
  [swampmonkey]

2.0.2 - 2010-09-09
------------------

- Forward port of a i18n fix from branches/1.2. It's used to create a
  changeset, the message doesn't seem to appear on the history view though.
  [vincentfretin]

- Added missing i18n markup to variables in ``update_version_before_edit.cpy``.
  [WouterVH]

2.0.1 - 2010-08-08
------------------

- Changed "version" to "revision" in portal messages.
  [kleist]

2.0 - 2010-07-18
----------------

- Changed the text in the `@@history` page to use the term revision instead of
  version. This fixes http://dev.plone.org/plone/ticket/10740.
  [hannosch]

- Added dependency on plone.app.blob, to pull in the needed bits for
  handling blobs in the modifiers.
  [davidblewett]

- Added event listeners for Archetypes' ObjectInitializedEvent and
  ObjectEditedEvent events (to go along with the existing WebDAV ones).
  [davidblewett]

- Changed Plone 3 backward compatible handling to also work with Chameleon.
  [do3cc]

2.0b9 - 2010-06-13
------------------

- Avoid dependency on zope.app.testing.
  [hannosch]

2.0b8 - 2010-05-20
------------------

- Added notification of changes on revert, via zope.lifecycle's
  ObjectModifiedEvent and Archetypes' ObjectEditedEvent.
  [davidblewett]

- Fixed revertversion.py so that it didn't tack on a lone / to the redirect
  URL.
  [davidblewett]

- Fixed CloneBlob & company, so that they check that the field provides an
  interface instead of using isinstance.
  [davidblewett]

- Fixed CloneBlob to not trample its local variables, allowing for multiple
  blob fields on a type.
  [davidblewett]

- Updated i18n methods that used mappings.
  [davidblewett]

2.0b7 - 2010-05-08
------------------

- Fix BLOB history corruption
  http://dev.plone.org/plone/ticket/10503
  [do3cc]

2.0b6 - 2010-04-20
------------------

- Widen html diff display to work better with new layout.
  [alecm]

- Fix issue with versioning of large folders.
  http://dev.plone.org/plone/ticket/10457
  [alecm]

2.0b5 - 2010-04-12
------------------

- Re-add title and description when viewing old versions in Plone 4.
  [davisagli]

2.0b4 - 2010-03-04
------------------

- Reverse order of diff listing on history view. Fixes
  http://dev.plone.org/plone/ticket/10119.
  [alecm]

- Fix version display when history is non-existent. Fixes
  http://dev.plone.org/plone/ticket/9674.
  [alecm]

2.0b3 - 2010-02-17
------------------

- Updated templates to follow recent markup conventions.
  References http://dev.plone.org/old/plone/ticket/9981.
  [spliter]

- Be more defensive in our importVarious step, to avoid issues while upgrading.
  [hannosch]

- Workaround for http//dev.plone.org/plone/ticket/10120, "version_history_form"
  now renders "Preview is not available." instead of causing a traceback.
  [kleist]

2.0b2 - 2009-12-27
------------------

- Fixed test dependencies and removed unused test helper code.
  [hannosch]

2.0b1 - 2009-12-02
------------------

- Fix dependence on global_defines in diff.pt.
  https://dev.plone.org/plone/ticket/9804
  [alecm]

2.0a1 - 2009-11-14
------------------

- Fix ordering issues with versioned BTree folders.
  [alecm]

- Make the Archetypes dependency a soft one.
  [alecm]

- Only make a copy of a BLOB if it's changed since the last save.
  Otherwise, just reference the BLOB from the prior revision.
  [alecm]

- Made the ZVCStorage store references directly in the shadow instead
  of simply passing them to ZVC.  This way real references can be used
  in the storage instead of copies, so that BLOB revisions can work.
  [alecm]

- Add modifiers to handle AT blob fields from plone.app.blob.  One
  handler skips the blobs and the other copies them.
  [alecm]

- Enable both inside and outside children modifiers by default for
  folder objects.  Using the INonStructuralFolder interface to determine
  which to use.
  [alecm]

- Fixes for reference handling in plone.folder and other BTree based folder implementations.
  [alecm]

- Added modifier that skips cloning of __parent__ pointers.
  [alecm]

- Switched document_byline macro to plone.belowcontenttitle content provider.
  [hannosch]

- Acquire plone_utils from context rather than assuming the putils global in
  templates.
  [erikrose]

- Fixed tests which depended on specific uids for portal content.
  Added cmf_uid catalog index in install profile.
  [alecm]

- Fixed missing i18n markup in versions_history_form.
  [hannosch]

- No longer rely on base_properties.
  [hannosch]

- Made some calls to portal_repository more defensive.
  [hannosch]

- Added the z3c.autoinclude entry point so this package is automatically loaded
  on Plone 3.3 and above.
  [hannosch]

- Use new import location for the package_home function.
  [hannosch]

- Added the required profile bits for installing CMFUid.
  [hannosch]

- Define dependency on Products.ZopeVersionControl.
  [hannosch]

- Define dependency on CMFDiffTool (via template using portal_diff) and
  avoiding a test dependency on CMFDefault.
  [hannosch]

- Define here_url in all templates and made get_macros not fail when
  encountering a browser view based template.
  [hannosch]

- Cleaned up package metadata and code to remove the dependency on Plone.
  [hannosch]

- Declare package dependencies and fixed deprecation warnings for use
  of Globals.
  [hannosch]

- Catch WebDAVObjectInitializedEvent/WebDAVObjectEditedEvent and
  save versions as appropriate. This is part of the fix for
  http://dev.plone.org/plone/ticket/7338
  [sidnei]

- Fixed the name of the file : is has to be the FileName not the Id [tbenita]

- Purged old Zope 2 Interface interfaces for Zope 2.12 compatibility.
  [elro]

- Fixed a bug in the file_download_version that prevented successful download
  of anterior version of files if the filename contained spaces. Anyway, the
  filename param of Content-Disposition header SHOULD NEVER come without
  double-quotes.
  [drjnut]

- Register GenericSetup steps via ZCML.
  [wichert]

- Use the new archetypes.edit.afterfieldsets viewlet manager to add our
  field to the AT edit template. The customized edit_macros is now no longer
  needed.
  [wichert]

1.2.7 - Unreleased
------------------

- Fix error in history storage selector calculation. Closes
  http://dev.plone.org/plone/ticket/8967.
  [alecm]

- Make "Revert to this version" on the versions_history_form an input
  with HTTP POST, instead of a simple GET link.
  Fixes http://dev.plone.org/plone/ticket/6932
  [maurits]

1.2.6 - December 2, 2009
------------------------

- Check history permissions in the context of the versioned object not
  the repository tool.  See http://plone.org/products/cmfeditions/issues/55
  [alecm]

- Fixed the html and javascript on the difference view so it works on
  more browsers.
  [vpretre, maurits]


1.2.5 - November 5, 2009
------------------------

- Show ndiff (natural diff) when neither inline diff nor html diff are
  available.
  [maurits]


1.2.4 - July 4, 2009
--------------------

- Fixed missing i18n markup in versions_history_form.
  [hannosch]


1.2.3 - July 4, 2009
--------------------

- Fix form action in @@history view.
  [vincentfretin]


1.2.2 - June 11, 2009
---------------------

- Fix XHTML markup for diff view.
  See ticket http://dev.plone.org/plone/ticket/9227
  [alecm]

1.2.1 - June 8, 2009
--------------------

- Add getHistoryMetadata method to allow efficient history display
  without full object retrieval.  Based on patches by Darryl Dixon on
  CMFEditions zvc_enfold_fixfailures branch r59908:60078.
  [alecm]


1.2 - May 16, 2009
------------------

- Add missing PACKAGE_HOME in the init file according to tests
  [encolpe]

- Add the encoding declaration (utf-8) in all python files
  [encolpe]

- Internationalization of 7 strings in diff.pt (history view).
  [vincentfretin]

- Fixed label_history_version msgid dynamic content in diff.pt (added i18n:name="version")
  [vincentfretin]


1.2b1 (March 7, 2009)
---------------------

- Register CMF skin layers via ZCML.
  [wichert]

- Remove history action. Plone 3.3 has alternative implementations in the
  form of the content history viewlet so this should not be installed by
  default.
  [wichert]

- Move import step registration to ZCML.
  [wichert]

- Use the new archetypes.edit.afterfieldsets viewlet manager to add our
  field to the AT edit template. The customized edit_macros is now no longer
  needed.
  [wichert]

- Some CMFEditions .py files use wrong MessageFactory (#8715)
  [encolpe]

- Set some msgids to cmfeditions i18n domain in version_file_view.
  Renamed msgid label_existing_keywords by label_existing_categories in
  version_metadata_view.
  [vincentfretin]


1.1.8 (October 6, 2008)
-----------------------

- Switch to egg-based distribution.
  [hannosch]

- Fix on FileDownloadVersion : files retrieved didn't get their version name
  [tbenita]

- Fix on FileDownloadVersion : files retrieved got corrupted at retrieval
  [drjnut]

- Merge AT changes into replacement of 'edit_macros.pt'.
  See ticket http://dev.plone.org/plone/ticket/7999.
  [rsantos]


1.1.7 (June 2, 2008)
--------------------

- Fix for issues with unicode version save comments.
  http://dev.plone.org/plone/ticket/7400
  [alecm]


1.1.6 (March 26, 2008)
----------------------

- Some i18n fixes to version_diff.pt. This closes
  http://dev.plone.org/plone/ticket/7862.
  [hannosch]

- Merge AT changes into our copy of 'edit_macros.pt'.
  See: http://dev.plone.org/plone/ticket/6936


1.1.5 (March 8, 2008)
---------------------

- Fix bug in wrapper assignment for some modifiers.
  [encolpe, alecm]

- Added metadata.xml file to the profile.
  [hannosch]


1.1.4 (December 6, 2007)
------------------------

- Add modifiers to avoid pickling extremely large files.  The
  AbortVersioningOfLargeFilesAndImages modifier is enabled by default
  for Files and Images. It will skip saving versions of objects when
  they contain a large file ('file' or 'image' field in Attribute or
  AnnotationStorage).  The SkipVersioningOfLargeFilesAndImages will
  simply not version the large file, but will version all other data.
  On retrieval it will put the file from the working copy in place.
  This is disabled by default, but can be enabled easily.
  Workaround for: http://dev.plone.org/plone/ticket/7223
  [alecm]


1.1.3 (December 2, 2007)
------------------------

- Make sure that we attempt to handle Inside Refs which have no
  portal_type, as well as retrieving revisions that once used the
  InsideRefsModifier but now use the OutsideRefsModifier.
  Related to: http://dev.plone.org/plone/ticket/7295
  [alecm]

- Fix issue on diff form where empty entries were being shown for
  unchanged files.  Related to http://dev.plone.org/plone/ticket/7253
  [alecm]

- Fix issues with purge policy as reported in
  http://dev.plone.org/plone/ticket/7300
  [alecm]

- Handle ArchivistUnregisteredErrors during save.  This occurs when an
  object has been imported, or when the version information has been
  destroyed.  Fixes http://dev.plone.org/plone/ticket/7334.
  [alecm]

- Reflect changes in base_edit.cpt asnd edit_macros.pt in r8683 of
  Archetypes: Skip the 'metadata' schema in base_edit, like we used to
  do it pre-1.5.  Also, do not render fieldset and legend elements
  when we're only displaying one fieldset, i.e. the 'default' one.
  [nouri]


1.1.2 (October 5, 2007)
-----------------------

- Added bits of missing i18n markup to versions_history_form.pt. This closes
  http://dev.plone.org/plone/ticket/7065.
  [hannosch, naro]

- Added CMFEditionsMessageFactory and used it to i18n-ize a statusmessages in
  revertversion.py. This closes http://dev.plone.org/plone/ticket/7066.
  [hannosch, naro]


1.1.1 (September 10, 2007)
--------------------------

- Expose the extra_top, widgets and extra_bottom METAL hooks in edit_macros.
  [wichert]


1.1-final (August 16, 2007)
---------------------------

- Prevent future off by one errors in the ui by just starting our count from 0.
  [alecm]

- Fix dumb acquisition issue in the default policy scripts.
  [alecm]

- Removed overly aggressive logging from update_version_before_edit.cpy.
  [hannosch]


1.1-rc1 (July 8, 2007)
----------------------

- Make text more consistent (use revision instead of version throughout the ui)

- Add checks in versioning policy scripts to ensure we don't get duplicate
  revisions.

- Add controller overrides so that the correct actions happen on
  cancel and reference upload.

- Add an event listener that removes the `version_id` attribute from
  copies.

- Removed i18n folder. Translations are shipped in PloneTranslations. [hannosch]

- Minor template corrections. [hannosch]


1.1-beta4 (April 30, 2007)
--------------------------

- Updated permission mapping to account for new local roles (Editor/Contributor)


1.1-beta3 (April 29, 2007)
--------------------------

- No longer register tools as utilities, since it broke the tests among
  other things.


1.1-beta2 (March 26, 2007)
--------------------------

- Register tools as utilities


1.1-beta1 (March 5, 2007)
-------------------------

- Make the AT autoversion policy save a version before the save for more
   intuitive behavior.

- Fixed numerous ui glitches on the versions history form and started using
   statusmessages.

- Do not install the versioning control panel anymore. You can enable versioning
  for a content type on the new types control panel now.

ToDo

- Finish exportimport handlers for portal_repository and portal_modifier thus
  making setuphandlers importVarious unnecessary again.

- Add back special portal_historyidhandler / portal_uidhandler handling. If a
  portal_uidhandler tool is found during install, it should be renamed to
  portal_historyidhandler. The missing tools should be created as normal then.


1.1-alpha2 (February 08, 2007)
------------------------------

- Removed specialized document byline.

- Switch to Plone control panel category


1.1-alpha1 (November 22, 2006)
------------------------------

Internal Changes

- Two minor updates for CMF 2.1 compatibility. [hannosch]

- Use a GenericSetup Extension profile for installation instead of an external
  method. [hannosch]

- Cleaned up tests. As these are based on PloneTestCase and Plone 3.0 we don't
  have to set up anything special anymore. [hannosch, alecm]

- Removed ActionProviderBase as a base class from all tools. In CMF 2.1 actions
  are usually only stored on the actions tool. [hannosch]

- Updated dependency information for Plone 3.0 inclusion. [hannosch]


1.0 (SVN)
---------

Bugs fixed

- Fixed OMInsideChildrensModifier InitializeClass. [encolpe]

Internal Changes

- Replaced usage of zLOG with Python's logging framework. [hannosch]

- Removed lots of unused import statements, found by pyflakes. [hannosch]

- Removed BBB code for old transaction handling. [hannosch]

- Removed some BBB code for ZClasses and CMF 1.4. [hannosch]

CMFEditions 1.0rc1 (unreleased)
-------------------------------

ToDo

- migration from CMFEditions 1.0alpha3 doesn't work correctly
- some translations are not yet updated: contact translators (for changes see
  below. Affected translations: fr, da, pl)
- Fix outstanding failing tests
- Some complex integration test with deleted version. (purge support)
- allow adding test hierarchy only if in debug mode
- allow migration in debug mode only
- fix issue #28
- fix issue #25
- fix issue #19
- fix issue #17
- fix issue #22

1.0beta1 (2006-06-24)
---------------------

Bugs fixed

- Fixed previewing (retrieving) files and images. [gregweb]

- Security Policy was for ``manage_setPolicies`` but the method name
  was ``manage_setTypePolicies``. Corrected. [gregweb]

- The storage now stores ZVC's ``__vc_info__`` for every version
  avoiding wrong information is attached to a working copy when
  previewing a version. Fix for ToDo.txt item #48. [gregweb]

- Replaced all occurences of ``rollback`` with ``revert``. Brought into
  sync internal names with UI. Rollback may suggest a transaction
  rollback which is something different. Including i18n label
  ``label_rollback`` which is now ``label_revert``. Added backwards
  compatibility code for configuration. Translations not updated.
  [gregweb]

- Minor refactorings of the version history view. Notably replaced
  ``(show below)`` by ``preview`` without jumping to the preview target
  on the page by default. Instead the link name of the previewed version
  changes to ``jump down``. [gregweb]

- The storage is now more immune against non int selectors. [gregweb]


Features Added

- The approximate size of a version is now recorded also at save time
  (and calculated at storage migartion).
  [gregweb]

- Added size information to storage statistics ZMI view [gregweb]

- Added German translations [gregweb]

- Added Polish translations provided by Piotr Furman [Piotr Furman, gregweb]

- ``RetainWorkflowStateAndHistory`` now adds the ``review_state`` to the
  ``sys_metadata`` at save time because at retreive time the workflow tool
  picks the working copies state. I didn't find any other way to do it
  without digging into workflows internals (which would have been a bad
  idea anyway). Had to extend the ``IModifier.ISaveRetrieveModifier``
  interface to allow a modifier enhance ``sys_metadata`` at save time.
  [gregweb]

- Added purge support [gregweb]:

  - Enhanced storage API with a ``purge`` method that inevitabely
    removes a version from the history. See added ``IPurgeSupport``
    and ``IPurgePolicy`` interfaces.
  - Purging raises an exception if no purge policy is installed. This
    will avoid a lot of future tracker items caused by people having
    removed the purge policy but nevertheless providing purge support
    to users. The reason is that the archivist and repo layer can't
    handle yet the empty placeholder object beeing returned by the
    storage for the purged version. This rule may be relaxed in future
    versions if the archivist and repo layer support handling of those
    empty placeholder objects.
  - The UI doesn't expose manual purge functionality. Through the ZMI a
    number n may be configured representing the maximum number of
    version per content item that have to be preserved. Older ones are
    automatically purged from the storage at save time.
  - There is a new purge permission that may be used to restrict purging
    to special roles if necessary (applicable to manual purging only).
  - On the repo layer (``portal_repository``) retrieving an object or
    iterating over the history always returns a valid (unpurged)
    version. The returned object may be a substitute. Two numbering
    schematas exist. Numbering counting purged versions and not
    counting purged versions (passing True or False to ``countPurged``).
    The default numbering schema is ``countPurged=True``. The UI
    history onyl shows unpurged versions (``countPurged=False``).
  - If the storage is asked to retreive a removed version it may be
    instructed to return a substitute for the removed version. The
    substitution policy itself is implemented in the new purge policy
    tool. This strategy allows to keep most purge implementation
    details out of the upper layers (archivist, modifiers, repository).
  - The new purge policy tool may be instructed to only keep n versions
    of a content item. Thus at save time the oldest version is purged
    if the save operation would result in more than n version reside in
    the storage.
  - The new purge policy tool substitutes a removed version with the
    next older version. If no other version is available the next
    newer is used as substitute. If none is available ... well this
    isn't yet tested :-)
  - The archivist and storage may be asked to also retreive the empty
    placeholder of a purged version. This functionality is yet exposed
    to the repo layer. This may change in a future release.
  - Added ``isValid`` method on the vdata object that allows to ask if
    the retrieved object it is valid or not (empty placeholder object
    or a real version).

- At save time a version aware reference to the parent node is saved
  also. Without it would be very ineffective or even impossible to
  find out the parents which potentially would prevent adding usefull
  features like retrieving the a whole site from one object in the
  tree. [gregweb]

- The histories default order has changed: It now returns the newest
  version as first item and the oldest as last item. The old behaviour
  is still available by passing ``oldestFirst=True``. [gregweb]

- Inserted the ``oldestFirst`` parameter before the already existing
  ``preserve`` parameter. This will cause changes of 3rd party products
  that are using ``preserve`` (None know at the moment, it's better to
  change now than later). [gregweb]

- Added two new i18n labels: ``label_preview_version_below``,
  ``label_preview_version`` (no translations yet) [gregweb]

- Renamed i18n label: ``label_show_below`` to ``label_preview_version_link``
  (updated labels in po-files but not the translations) [gregweb]


Internal Changes

- Now save all metadata also in shadow storage. But currently on retrieve
  the metadata is still feteched from the ZVC storage. [gregweb]

- Added migration code for 1.0alpha3 --> 1.0beta1 storage migrations
  [gregweb]

- Adding purge support caused heavy refactoring the version storage.
  ZVC is still used to store the contents history but now additional
  data is stored in a parallel shadow storage. The layout of the data
  in the ZVC didn't change, only ZVC and purge related metadata has
  been added to the parallel shadow storage. [gregweb]

- Garbage collected a lot of code that was commented out, outdated
  triple-X's and items in ``ToDo.txt``. [gregweb]

- The storage tests now tests ZVCSTorageTool only once and additionally
  tests the dummy memory storage. This was the intended behaviour but
  a bug prevented running the tests with the dummy storage and instead
  run the tests with ZVCStorageToll twice. [gregweb]


1.0alpha4 (2006-06-24)
----------------------

Bugs fixed

- fixed bug with AT references causing ref catalog having been inconsistent
  [sunew]


Features added

- Comment is now taken from request if any. [sunew]

- Added storage statistics ZMI view. [gregweb]

- Added functionality to create a test hierarchy. [gregweb]


1.0alpha3 (2006-06-03)
----------------------

Bugs fixed

- Fixed tracker issue #15 [alecm, gregweb]

- When previewing a version the expandable history link is removed as this
  doesn't make sense at all and caused double fetching of history items.
  [gregweb]

- Use the default view of the retrieved object, as it may be different from
  that of the current object. [alecm]

- The expandable version link is only shown for users having the permission
  to view the history. [rafrombrc]

- Added RetainATRefs modifier [vds]

- Fixed broken ``isUpToDate`` [gregweb]

- ``version_id`` wasn't correctly set at the working copy at save time.
  Because of this it may happen that the wrong version info was saved
  with the version aware reference. The version_id is now set at the end
  of the save operation. [alecm, gregweb]

- Handle usecase where an inside reference is moved outside its container.
  Still need to handle case where it has been replaced by another object
  with the same id.  [alecm]

- Changed API for Archivist methods and the dereference utility method so
  that they now accept an optional history_id, rather than implicitly
  allowing the 'obj' parameter to be a history_id. As side effect this
  will help in supporting multi location checkout in the future.
  [alecm, gregweb]

- Fixed various UI issues. [rlemmi, vds, alecm]

- Fixed SF issue #1376836. [alecm]

- restored at's extra_buttons slot (some others slots are still missing
  because of this template override) [syt]

- Totally refactored recursive retrieve of an ancient version of an object.
  Fixed a lot of folderish bugs with this refactoring. [gregweb]

- Corrected a hairy acquisition bug that caused wrong security evaluations
  (ArchivistTool.py). Acquisition is a monster feature! [gregweb]

- The storage now returns obj.modified() instead of
  obj.getModificationDate() because it's more fine graned. [gregweb]

- Added ReferenceFactoriesTool.py which in essence knows how to
  instatiate a reference. The current implementation is inflexible and
  knows only how to instantiate object into an ObjectManager. This
  is the first step in preparation for AT reference handling. [gregweb]

- Fixed tracker issue #16 RuntimeError: maximum recursion depth exceeded.
  I (gregweb) suspect it got fixed by: [alecm]

- Fixed identical tracker issues #5, #6, #7, #8. I (gregweb) suspect it got
  fixed by: [alecm]

- Added modifier to copy permissions from working copy onto retrieved
  versions, otherwise retaining workflow can have some very strange
  consequences. [alecm]

- Fixed a number of bugs involving handling of adding and deleting subobjects
  of versioned folders.
  [alecm]

- Fixed a permissions bug which made the versions_history_form inaccessible if
  any of the versions were saved while private (or otherwise had
  'Access contents information' disabled).
  [alecm]

- Made quickinstalled product reinstall/uninstall work without issue.  Fixed
  unit tests for Plone 2.1.  Use mutators in templates and tests where
  applicable rather than direct attribute access. Was Issue #9, #10 and #11.
  Thanks to Andrew Lewis for the patches and reports. [Andrew Lewis, alecm]

- Corrected bugs in ``RetainWorkflowStateAndHistory`` modifier and the
  modifier registry avoiding the review state and the workflow history
  from beeing retained on retrieve and revert.


Features added

- Added danish translation. [stonor]

- Retrieving an object just for preview (without replacing the working copy)
  caused a lot of headaches and got more and more complex und ununderstandable.
  Everything got much simpler by just using a savepoint/abort pair at the right
  place while retrieving. [alecm]

- I18N tuned (diff-legend untested), french added
  [Gpgi, gotcha]

- Added more tests to improve coverage. [azy, vds, alecm]

- Added support for ATCT (Archetypes Content Types). [azy]

- Added ZMI interface for modifiers. [rlemmi]

- It's now possible to save a new version in the edit view. As soon as a
  version sahll be saved a comment field is inserted to add a comment.
  [rlemmi]

- Added expandable version history to document_byline. [rlemmi]

- Made the ModifierRegistryTool make use of any preserve dict passed back to
  it by afterRetrieveModifiers.
  [alecm]

- Added optional CMFDiffTool support for generating diffs between object
  versions.  For this to work you need to setup the diffable fields on each
  type in portal_diff.  In the 'alecm-at-schema-diffs' branch of CMFDiffTool
  there is a diff type that can be applied to any AT object which will
  automatically setup diffs for all fields in the schema (when using this
  any value can be entered for the field in portal_diff).
  [alecm]

- Added a versioning policy (at_edit_autoversion) which automatically creates
  new versions on edit for AT types which are configured to support the policy
  in the configlet.  This is implemented using a simple macro override on
  AT's edit_macros, and a new entry in the AT edit form controller chain.
  [alecm]

- Added new interface IContentTypeVersionPolicySupport and implemented it in
  portal_repository.  It allows products to register versioning policies
  (classes which implement IVersionPolicy), and to associate those policies
  with specific portal types.  IVersionPolicy objects may define methods
  (setupPolicyHook, removePolicyHook, enablePolicyOnTypeHook,
  disablePolicyOnTypeHook) which can be used to install/uninstall policy
  specific behavior in the portal, on adding/removing the policy, or enabling/
  disabling the policy on a specific type.
  [alecm]


1.0alpha2 (around June 2005)
----------------------------

no changes recorded
