## Script (Python) "onEditChangeSet"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=id1, id2
##title=Compute object differences
##

retrieve = context.portal_repository.retrieve

if id1 == 'current':
    ob1 = context
else:
    ob1 = retrieve(context, int(id1)).object

ob2 = retrieve(context, int(id2)).object
base_id = ob1.getId()
diff = context.portal_diff.createChangeSet(ob2, ob1,
                                           id1=ob2.getId()+' (rev. %s)'%id2,
                                           id2=ob1.getId()+' (rev. %s)'%id1)
return diff