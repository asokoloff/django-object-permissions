from django.test import TestCase

from models import Party, PermissionableObject, PartyPrivilege
from django.db import models
from utils import update_permission_ancestor_data

# See:
# http://stackoverflow.com/questions/502916/django-how-to-create-a-model-dynamically-just-for-testing
# for instructions on how to make models for testing only

# Subclasses for testing purposes only. These are only loaded by the
# test runner

class Person(Party):
    name = models.CharField(max_length=100)

class W(PermissionableObject):
    name = models.CharField(max_length=100)

class X(PermissionableObject):
    permission_parent_classes = [W]
    name = models.CharField(max_length=100)
    w = models.ForeignKey(W)

class Y(PermissionableObject):
    permission_parent_classes = [X]
    name = models.CharField(max_length=100)
    x = models.ForeignKey(X)

class Z(PermissionableObject):
    permission_parent_classes = [Y]
    name = models.CharField(max_length=100)
    y = models.ForeignKey(Y)


class TestObjectPerms(TestCase):

    def setUp(self):
#         w = W.objects.create(name='foo')
#         x = X.objects.create(name='bar',w=w)
#         y = Y.objects.create(name='baz',x=x)
#         Z.objects.create(name='bif',y=y)

        Person.objects.create(name='fred')

    def test_person_exists(self):
        self.assertTrue(Person.objects.filter(name='fred').count() == 1)


    def test_ancestor_paths(self):

        self.assertTrue(W._get_ancestor_paths() == ['w'])
        Z_ancestors = Z._get_ancestor_paths()
        self.assertTrue(len(Z_ancestors) == 4)
        expected_set = set(['z', 'z.y', 'z.y.x', 'z.y.x.w'])
        self.assertTrue(set(Z_ancestors) == expected_set)

    def test_ancestor_object_retrieval(self):

        w = W()
        w.name = 'w'
        w.save()
        update_permission_ancestor_data(w)

        x = X()
        x.name = 'x'
        x.w = w
        x.save()
        update_permission_ancestor_data(x)

        y = Y()
        y.name = 'y'
        y.x = x
        y.save()
        update_permission_ancestor_data(y)

        z = Z()
        z.name = 'z'
        z.y = y
        z.save()
        update_permission_ancestor_data(z)

        update_permission_ancestor_data(w)

        top_object = W.objects.get(name='w')
        self.assertTrue(len(top_object.get_permission_ancestors()) == 1)
        self.assertTrue(top_object.get_permission_ancestors()[0].__class__ == PermissionableObject)
        bottom_object = Z.objects.get(name='z')

        self.assertTrue(len(bottom_object.get_permission_ancestors()) == 4)



#     def test_direct_permission(self):
#         o = Z.objects.get(name='bif').permissionableobject_ptr
#         qset = Z._get_descendant_objects([o.id])
#         self.assertTrue(qset.count() == 1)
#         self.assertTrue(qset[0].name == 'bif')

#     def test_inherited_permission(self):
#         o = W.objects.get(name='foo').permissionableobject_ptr
#         # should inherit down to x, y, z
#         qset = Z._get_descendant_objects([o.id])
#         self.assertTrue(qset.count() == 1)
#         self.assertTrue(qset[0].name == 'bif')

#     def test_permission_assignment(self):
#         p = Person.objects.get(name='fred').party_ptr
#         o = W.objects.get(name='foo').permissionableobject_ptr 
#         # o = Z.objects.get(name='bif').permissionableobject_ptr
#         PartyPrivilege.objects.create(party=p,permissionable_object=o,privilege='admin')
#         # Fred has admin privileges on a single W object.
#         qset = Z.get_permitted_items(p,'admin')
#         self.assertTrue(qset.count() == 1)
#         self.assertTrue(qset[0].name == 'bif')



