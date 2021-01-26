Let's import our mock objects and the modifiers we'd like to test::

    >>> from Products.CMFEditions.tests.test_doctests import DummyFile
    >>> from Products.CMFEditions.tests.test_doctests import DummyContent
    >>> from Products.CMFEditions.StandardModifiers import AbortVersioningOfLargeFilesAndImages
    >>> from Products.CMFEditions.StandardModifiers import SkipVersioningOfLargeFilesAndImages
    >>> from Products.CMFEditions.StandardModifiers import LargeFilePlaceHolder
    >>> from Products.CMFEditions.Modifiers import ConditionalTalesModifier
    >>> from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError


Abort when Versioning Big Files
===============================

We'll start with the simple AbortVersioningOfLargeFilesAndImages
modifier.  It should detect files stored in attributes
which exceed a certain threshold size and raise an exception.  It should
be configurable using a tal expression.

Let's set up our modifier, and verify that it's edit method sets the
expected values::

    >>> modifier = AbortVersioningOfLargeFilesAndImages()
    >>> isinstance(modifier, ConditionalTalesModifier)
    True
    >>> modifier.max_size
    26214400
    >>> modifier.field_names
    ('file', 'image')
    >>> modifier.edit(field_names='my_file \n my_image', max_size=1000)
    >>> modifier.max_size
    1000
    >>> modifier.field_names
    ('my_file', 'my_image')
    >>> print(modifier.getFieldNames())
    my_file
    my_image
    >>> modifier.getModifier() is modifier
    True

Now we make a content object to test with and verify that the modifier
performs no actions on the object by default during object cloning::

    >>> content = DummyContent('dummy')
    >>> modifier.getOnCloneModifiers(content) is None
    True

When we store a file in an attribute which has a size greater than
or equal to the specified size, we will get an error.  If the
file object is smaller no error will be raised::

    >>> modifier.getOnCloneModifiers(content)
    >>> content.my_image = DummyFile(1000)
    >>> try:
    ...     modifier.getOnCloneModifiers(content)
    ... except FileTooLargeToVersionError:
    ...     print('exception')
    exception

    >>> content.my_image.size = 999
    >>> modifier.getOnCloneModifiers(content)


Skip Versioning of Large File Attributes
========================================

Now let's test the alternate modifier, which tells the pickler to
replace large file attributes with a marker to avoid pickling them.
We'll make our modifer and set some defaults as above, and then add to
it file and image attributes::

    >>> modifier = SkipVersioningOfLargeFilesAndImages()
    >>> isinstance(modifier, AbortVersioningOfLargeFilesAndImages)
    True
    >>> modifier.edit(field_names='file \n image \n image2',
    ...               max_size=1000)
    >>> content = DummyContent('dummy')
    >>> modifier.getOnCloneModifiers(content) is None
    True
    >>> content.image = image = DummyFile(1000)
    >>> content.image2 = image2 = DummyFile(999)


Cloning
-------

When it finds over-sized files the modifier will return a persistent
id generating function for the pickler, a persistent_load function that
resolves a given id to the desired object, and two lists of referenced
objects.  This modifier does not handler object references so both lists
will be empty.  The persistent_id function will simply return True for
all objects which need to be replaced, and None for others, and the
persistent loader just returns a placeholder object::

    >>> pers_id, pers_load, empty, empty2 = modifier.getOnCloneModifiers(content)
    >>> empty
    []
    >>> empty2
    []
    >>> pers_id(image2) is None
    True
    >>> pers_id(image)
    True
    >>> isinstance(pers_load(True), LargeFilePlaceHolder)
    True

Retrieval
---------

On retrieving an object from storage the modifier's afterRetrievedModifier
method will be called with the working copy and cloned objects.  This will
alter the clone, replacing any placeholders on the object from the
working copy.

Let's mockup a cloned object with LargeFilePlaceHolders in place::

    >>> clone = DummyContent('dummy')
    >>> clone.image = LargeFilePlaceHolder()
    >>> clone.image2 = DummyFile(300)
    >>> clone.image is not content.image
    True

Now if we use the afterRetrievedModifier to manipulate the clone we should
have our placeholders replaced by instances from the working copy::

    >>> empty = modifier.afterRetrieveModifier(content, clone)
    >>> clone.image is content.image
    True
    >>> clone.image2 is content.image2
    False
    >>> clone.image2.getSize()
    300

If the attribute has been removed from the working copy, it will be removed
from the clone::

    >>> clone.image = LargeFilePlaceHolder()
    >>> del content.image
    >>> empty = modifier.afterRetrieveModifier(content, clone)
    >>> hasattr(clone, 'image')
    False

    >>> clone.image = LargeFilePlaceHolder()
    >>> empty = modifier.afterRetrieveModifier(content, clone)
