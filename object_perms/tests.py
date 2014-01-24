from django.test import TestCase
from models import Party, PermissionableObject, PartyPrivilege, \
    PermissionAncestor
from django.db import models
from utils import update_permission_ancestor_data

# Subclasses for testing purposes only. These are only loaded by the
# test runner

class Person(Party):
    name = models.CharField(max_length=100)


class W(PermissionableObject):
    name = models.CharField(max_length=100)


class X(PermissionableObject):
    name = models.CharField(max_length=100)
    w = models.ForeignKey(W)
    
    @property
    def permission_parents(self):
        return [self.w]


class Y(PermissionableObject):
    name = models.CharField(max_length=100)
    x = models.ForeignKey(X)

    @property
    def permission_parents(self):
        return [self.x]


class Z(PermissionableObject):
    name = models.CharField(max_length=100)
    y = models.ForeignKey(Y)

    @property
    def permission_parents(self):
        return [self.y]


class TestObjectPerms(TestCase):

    def setUp(self):
        Person.objects.create(name='fred')

    def test_person_exists(self):
        self.assertTrue(Person.objects.filter(name='fred').count() == 1)

    def create_test_instances(self, **kwargs):
        w = W()
        w.name = 'w'
        w.save(**kwargs)

        x = X()
        x.name = 'x'
        x.w = w
        x.save(**kwargs)

        y = Y()
        y.name = 'y'
        y.x = x
        y.save(**kwargs)

        z = Z()
        z.name = 'z'
        z.y = y
        z.save(**kwargs)

        return w, x, y, z

    def test_get_permission_ancestors(self):
        kwargs = {'update_ancestors': False}

        w, x, y, z = self.create_test_instances(**kwargs)

        self.assertTrue(len(w.get_permission_ancestors()) == 1)
        self.assertTrue(w.get_permission_ancestors()[0].__class__ == PermissionableObject)
        self.assertTrue(len(z.get_permission_ancestors()) == 4)

    def test_update_ancestors(self):

        kwargs = {'update_ancestors': False}

        w, x, y, z = self.create_test_instances(**kwargs)

        # at this point, none of the objects should have ancestor data
        # populated.
        for item in [w, x, y, z]:
            stored_ancestor_count = PermissionAncestor.objects.filter(child_object=item).count()
            self.assertTrue(stored_ancestor_count == 0)

        # trigger populate of PermissionAncestor
        for instance in z, y, x, w:
            update_permission_ancestor_data(instance)

        w2 = W.objects.create(name='w2')
        x.w = w2
        x.save(**kwargs)

        # at this point, x, y, and z should have stale data in
        # PermissionAncestor.
        for instance in x, y, z:
            stored_ancestors = PermissionAncestor.objects.filter(
                child_object=instance
                )
            derived_ancestors = instance.get_permission_ancestors()
            self.assertFalse(
                set([a.id for a in derived_ancestors]) == set([b.ancestor_object_id for b in stored_ancestors])
                )

        # this should trigger refresh of data for x, y, z
        x.save()
        for item in x, y, z:
            stored_ancestors = PermissionAncestor.objects.filter(
                child_object=item
                )
            derived_ancestors = item.get_permission_ancestors()
            self.assertTrue(
                set([a.id for a in derived_ancestors]) == set([b.ancestor_object_id for b in stored_ancestors])
                )

    def test_integration_for_update_ancestors(self):
        # create a new set of instances with save method to update
        # ancestors activated
        w, x, y, z = self.create_test_instances()
        for index, item in enumerate([w, x, y, z]):
            stored_ancestors = PermissionAncestor.objects.filter(
                child_object=item
                )
            derived_ancestors = item.get_permission_ancestors()
            self.assertTrue(len(derived_ancestors) == index + 1)
            self.assertTrue(
                set([a.id for a in derived_ancestors]) == set([b.ancestor_object_id for b in stored_ancestors])
                )
        
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



