from django.db import models
from django.db.models import Q
import operator

PRIVILEGES = (
    ('admin', 'Administer'),
    ('read', 'Read'),
    ('edit', 'Edit'),
    ('delete', 'Delete'),
)

class Party(models.Model):
    
    parent_party = models.ForeignKey(
        'Party',
        blank=True,
        null=True,
        related_name='child_parties'
        )

    inherit_permissions = models.BooleanField(default=False)


class PermissionableObject(models.Model):

    permission_parent_classes = list()

    @classmethod
    def get_permissioned_objects(cls, directly_permed_objects):
        """ 
        Expects a list of permissionableobject ids over which the user has
        direct privileges. Builds a query that searches for matches in
        the curent model or any model the current model inherits
        permissions from using Q objects.  Returns a query set of
        objects over which the user has either direct or inherited
        privileges.
        """
        q_params = list()
        q_params.append('permissionableobject_ptr_id__in')
        for p_class in cls.permission_parent_classes:
            q_params.extend(
                [x + '__permissionableobject_ptr_id__in' for x in \
                                 p_class._get_parent_privilege_paths()]
                )
        query_predicates = [(x, directly_permed_objects) for x in q_params]
        q_list = [Q(x) for x in query_predicates]
        return cls.objects.filter(reduce(operator.or_, q_list))

    @classmethod
    def _get_parent_privilege_paths(cls):
        """
        Builds a set of paths to parent objects for permission query
        builder.
        """
        all_paths = list()
        for x in cls.permission_parent_classes:
            for path in x._get_parent_privilege_paths():
                all_paths.append(cls.__name__.lower() + '__' + path)
        all_paths.append(cls.__name__.lower())
        return all_paths                            

    
class PartyPrivilege(models.Model):
    
    party = models.ForeignKey(Party)
    object = models.ForeignKey(PermissionableObject)
    privilege = models.CharField(
        max_length=100,
        choices=PRIVILEGES
        )

    class Meta:
        unique_together = ('party', 'object')


# subclasses for testing purpose only

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
