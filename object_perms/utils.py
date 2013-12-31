from model import PermissionableObject, PermissionAncestor


def get_direct_permissions(party, privilege):
    PermissionableObject.objects.filter(
        partyprivilege__party__in=party.get_memberships(),
        partyprivilege__privilege=privilege
        )

def update_permission_ancestor_data(permissionable_object):
    derived_ancestors = party.get_permission_ancestors()
    stored_ancestors = PermissionAncestor.objects.filter(child_object=permissionable_object)

    # check if anything has changed
    if set([x.id for x in derived_ancestors]) == set([x.ancestor_object_id for x in stored_ancestors]):
            return
    # FIXME: add transaction handling
    PermissionAncestor.objects.filter(child_object=permissionable_object).delete()
    for ancestor in derived_ancestors:
        PermissionAncestor.objects.create(child_object=self,ancestor_object=ancestor)

def update_child_ancestor_data(permissionable_object):
        """
        Uses PermissionAncestor to find child
        objects. InheritanceManager (select_subclasses queryset
        method) returns subclass instances that we need.
        """
        permission_children = PermissionableObject.objects.filter(
            permission_ancestors__ancestor_object=permissionable_object
            ).select_subclasses()
        for child in permission_children:
            child._update_permission_ancestor_data()

