from django.db import models
from model_utils.managers import InheritanceManager

PRIVILEGES = (
    ('admin', 'Administer'),
    ('read', 'Read'),
    ('edit', 'Edit'),
    ('delete', 'Delete'),
)


class Party(models.Model):

    def get_memberships(self, require_permissions_inherit=True):
        """
        recursively identify group memberships
        """
        result = [self]
        for item in self.memberships:
            if item.inherit_permissions or not require_permissions_inherit:
                result.extend(item.member_of.get_memberships())
        return result


class Membership(models.Model):

    member = models.ForeignKey(
        'Party',
        related_name='memberships'
        )

    member_of = models.ForeignKey(
        'Party',
        related_name='members'
        )

    inherit_permissions = models.BooleanField(default=False)


class PermissionableObject(models.Model):

    permission_parent_classes = list()
    objects = InheritanceManager()

    def __unicode__(self):
        return "id: {0}".format(self.id)

    @classmethod
    def get_permitted_items(cls, party, privilege):
        from utils import get_direct_permissions
        direct_permissions = get_direct_permissions(party, privilege)
        return cls.objects.filter(
            permissionableobject_ptr__permission_ancestors__ancestor_object__in=direct_permissions
            ).distinct()

    @classmethod
    def _get_ancestor_paths(cls):
        """
        Recursively adds paths to parent objects when calculating
        permission ancestors.
        """
        all_paths = list()
        this_segment = cls.__name__.lower()
        for x in cls.permission_parent_classes:
            for path in x._get_ancestor_paths():
                all_paths.append('{0}.{1}'.format(this_segment, path))
        all_paths.append(this_segment)
        return all_paths                            

    def get_permission_ancestors(self):
        """
        Calculates objects that the present object inherits
        permissions from using fk relations in subclasses. Returns
        list of instances of PermissionAncestor (not subclass).
        """
        ancestor_str = list()
        for x in self.__class__.permission_parent_classes:
            for path in x._get_ancestor_paths():
                ancestor_str.append('self.{0}.permissionableobject_ptr'.format(path))
        ancestor_str.append('self.permissionableobject_ptr')
        return [eval(x) for x in ancestor_str]

    def save(self, *args, **kwargs):
        from utils import update_permission_ancestor_data
        update_ancestors = kwargs.pop('update_ancestors', True)
        super(PermissionableObject, self).save(*args, **kwargs)
        if update_ancestors:
            update_permission_ancestor_data(self)

class PermissionAncestor(models.Model):
    """
    The data in this model is derived using the foreign key
    relationships of tables that subclass PermissionableObject. For a
    given permissionable object, this model records all of the other
    permissionable objects from which the first object inherits
    permissions, including the object itself. The purpose of storing
    the data in this form is to allow simple queries that traverse
    object hierarchies of any depth.
    """

    child_object = models.ForeignKey(
        PermissionableObject,
        related_name='permission_ancestors'
        )

    ancestor_object = models.ForeignKey(
        PermissionableObject,
        related_name='permission_children'
        )

    class Meta:
        unique_together = ('child_object', 'ancestor_object')


class PartyPrivilege(models.Model):
    
    party = models.ForeignKey(Party)
    permissionable_object = models.ForeignKey(PermissionableObject)
    privilege = models.CharField(
        max_length=100,
        choices=PRIVILEGES
        )

    class Meta:
        unique_together = ('party', 'permissionable_object', 'privilege')

