from django.test import TestCase

from models import Person, W, X, Y, Z, PartyPrivilege

class TestObjectPerms(TestCase):

    def setUp(self):
        w = W.objects.create(name='foo')
        x = X.objects.create(name='bar',w=w)
        y = Y.objects.create(name='baz',x=x)
        Z.objects.create(name='bif',y=y)

        Person.objects.create(name='fred')

    def test_person_exists(self):
        self.assertTrue(Person.objects.filter(name='fred').count() == 1)

    def test_direct_permission(self):
        # p = Person.objects.get(name='fred').party_ptr
        o = Z.objects.get(name='bif').permissionableobject_ptr
        # PartyPrivilege.objects.create(party=p,object=o,privilege='admin')

        # Fred has admin privileges on are single Z object.
        qset = Z.get_permissioned_objects([o.id])
        self.assertTrue(qset.count() == 1)
        self.assertTrue(qset[0].name == 'bif')

    def test_inherited_permission(self):
        # p = Person.objects.get(name='fred').party_ptr
        o = W.objects.get(name='foo').permissionableobject_ptr

        # PartyPrivilege.objects.create(party=p,object=o,privilege='admin')

        # Fred has admin privileges on are single W object, and this
        # should inherit down to x, y, z
        qset = Z.get_permissioned_objects([o.id])
        self.assertTrue(qset.count() == 1)
        self.assertTrue(qset[0].name == 'bif')



# class SimpleTest(TestCase):
#     def test_basic_addition(self):
#         """
#         Tests that 1 + 1 always equals 2.
#         """
#         self.assertEqual(1 + 1, 2)
