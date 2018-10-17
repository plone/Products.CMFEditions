WebDAV and Versioning
=====================

This doctest makes sure that WebDAV changes to Archetypes-based
objects trigger versioning correctly:

  >>> from plone.app.testing import TEST_USER_ID
  >>> from plone.app.testing import TEST_USER_NAME
  >>> from plone.app.testing import TEST_USER_PASSWORD

Doing a `PUT` request that creates a brand new object, and so should
create and save an initial version as happens when creating a brand
new object via the Plone UI:

  >>> from plone.app.testing import setRoles
  >>> portal = layer['portal']
  >>> setRoles(portal, TEST_USER_ID, ['Manager'])
  >>> fti = portal.portal_types['Document']
  >>> behaviors = list(fti.behaviors)
  >>> behaviors.append('plone.app.versioningbehavior.behaviors.IVersionable')
  >>> fti.behaviors = tuple(behaviors)
  >>> folder_id = portal.invokeFactory('Folder', 'folder')
  >>> folder = portal[folder_id]
  >>> folder_path = '/'.join(folder.getPhysicalPath())
  >>> 'some-document' in folder.objectIds()
  False

  >>> from ZServer.Testing.doctest_functional import http
  >>> from Testing.ZopeTestCase.sandbox import AppZapper
  >>> AppZapper().set(layer['app'])
  >>> print http(r"""
  ... PUT /%s/some-document HTTP/1.1
  ... Authorization: Basic %s:%s
  ... Content-Type: text/plain; charset="utf-8"
  ...
  ... Some Content
  ... """ % (folder_path, TEST_USER_NAME, TEST_USER_PASSWORD))
  HTTP/1.1 201 Created
  ...

  >>> 'some-document' in folder.objectIds()
  True

  >>> print(folder['some-document'].text.raw)
  Some Content


There should be only one history entry and not two or more

TODO: In Dexterity there are 2 entries. Why?

  >>> portal_repo = portal.portal_repository
  >>> len(portal_repo.getHistory(folder['some-document']))
  2

Doing another `PUT` request to update the same object should cause
another version of the object to be saved:

TODO: The result should be 'HTTP/1.1 204 No Content' but
In Dexterity it is 'HTTP/1.1 200 OK' instead.

  >>> print http(r"""
  ... PUT /%s/some-document HTTP/1.1
  ... Authorization: Basic %s:%s
  ... Content-Type: text/plain; charset="utf-8"
  ...
  ... Some Other Content
  ... """ % (folder_path, TEST_USER_NAME, TEST_USER_PASSWORD))
  HTTP/1.1 200 OK
  ...

  >>> print(folder['some-document'].text.raw)
  Some Other Content

TODO: In Dexterity there are now 3 entries instead of the expected two (see above).

  >>> len(portal_repo.getHistory(folder['some-document']))
  3

Creating a folder does not trigger a revision because the policy is
not configured for folders:

  >>> print http(r"""
  ... MKCOL /%s/some-folder HTTP/1.1
  ... Authorization: Basic %s:%s
  ... """ % (folder_path, TEST_USER_NAME, TEST_USER_PASSWORD))
  HTTP/1.1 201 Created
  ...

  >>> len(portal_repo.getHistory(folder['some-folder']))
  0

Note: If you use Appzapper you also need to use clear as teardown to prevent
spilling to other testlayers:

  >>> AppZapper().clear()
