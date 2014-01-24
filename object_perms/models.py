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

    objects = InheritanceManager()

    def __unicode__(self):
        return "id: {0}".format(self.id)

    @classmethod
    def get_permitted_items(cls, party, privilege):
        if cls is PermissionableObject:
            raise TypeError('get_permitted_items cannot be called on base model PermissionableObject')
        from utils import get_direct_permissions
        direct_permissions = get_direct_permissions(party, privilege)
        return cls.objects.filter(
            permissionableobject_ptr__permission_ancestors__ancestor_object__in=direct_permissions
            ).distinct()

    @property
    def permission_parents(self):
        return []

    def get_permission_ancestors(self):
        """
        For our purposes, permission ancestors includes the object
        this method is originally called on. Recursively gathers
        parent objects using foreign key relations specifid in property
        permission parents.
        """
        # Don't call this with instances of base Model
        if self.__class__ is PermissionableObject:
            raise TypeError(
                'get_permission_ancestors cannot be called on instances of the base model PermissionableObject'
                )

        return [x.permissionableobject_ptr for x in self._get_permission_ancestors()]

    def _get_permission_ancestors(self):
        ancestors = [self]
        for parent in self.permission_parents:
            ancestors.extend(parent._get_permission_ancestors())
        return ancestors
            
    def save(self, *args, **kwargs):
        update_ancestors = kwargs.pop('update_ancestors', True)
        super(PermissionableObject, self).save(*args, **kwargs)
        # only run for instances of subclasses
        if update_ancestors and self.__class__ is not PermissionableObject:
            from utils import update_permission_ancestor_data
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

