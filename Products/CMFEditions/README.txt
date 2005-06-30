CMFEditions is a tool for versioning the objects in a CMF or Plone Site. 
It is splitten into three layers: repository, archivist and storage. Repository is just
a basic tool, which offers the functionality for storing and retrieving the object. 
Archivist is a tool which allows you to customise the way in which the objects
are stored, and finally, the storage is storing the versions of the
objects. We assume nothing about the object we are going to version, the same
applies to the references between objects. 

XXX More to be written.

   ------------------------------------------------------------------------
   |                         portal_repository                            |
   |                                                                      |
   ------------------------------------------------------------------------
   |                         portal_archivist                             |
   |                                                                      |
   |               -------------------------------------------------------|
   |               |               portal_modifier (registry)             |
   |               |                                                      | 
   |               |   -----    -----   -----   -----                     |
   |              ====>|    |==>|   |==>|   |==>|   |                     |
   |               |   | M1*|   |M2*|   |M3*|   |M4*|  ........           |
   |              <====|    |<==|   |<==|   |<==|   |                     |
   |               |   -----    -----   -----   -----                     |
   |               -------------------------------------------------------|
   |                                                                      |
   -----------------------------------------------------------------------|
   |                         portal_storage                               |
   |                                                                      |
   |                                                                      |
   -----------------------------------------------------------------------|
		     
   * M1, M2... are modifiers
