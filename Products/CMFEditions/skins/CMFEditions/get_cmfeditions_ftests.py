## Script (Python) "get_cmfeditions_ftests"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=get cmfeditions ftests
##
selenium = context.portal_selenium
suite = selenium.getSuite()
target_language='en'
suite.setTargetLanguage(target_language)

selenium.addUser(id = 'sampleadmin',fullname='Sample Admin',roles=['Member', 'Manager',])

# 1
test_logout = suite.TestLogout()
test_admin_login  = suite.TestLoginPortlet('admin')

suite.addTests("CMFEditions",
          'Login as Sample Admin',
          test_logout,
          test_admin_login,
          "check versions tab",
          suite.open('/index_html'),
          suite.verifyTextPresent("versions"),
         )

return suite
