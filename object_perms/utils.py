from models import PermissionableObject, PermissionAncestor

def assign_permission(permissionable_object, party, permission):
    pass

def has_permission(permissionable_object, party, permission):
    pass

def get_direct_permissions(party, privilege):
    PermissionableObject.objects.filter(
        partyprivilege__party__in=party.get_memberships(),
        partyprivilege__privilege=privilege
        )

def update_permission_ancestor_data(po_subclass_instance, check_ancestor_changes=True):
    """
    Expects an instance of a subclass of PermissionableObject. Called
    recursively for objects that inherit permissions from passed object.
    """
    derived_ancestors = po_subclass_instance.get_permission_ancestors()

    if check_ancestor_changes:
        # check if anything has changed
        stored_ancestors = PermissionAncestor.objects.filter(child_object=po_subclass_instance)
        if set([x.id for x in derived_ancestors]) == set([x.ancestor_object_id for x in stored_ancestors]):
            return

    PermissionAncestor.objects.filter(child_object=po_subclass_instance).delete()
    for ancestor in derived_ancestors:
        PermissionAncestor.objects.create(child_object=po_subclass_instance,ancestor_object=ancestor)

    # select_subclasses is a query method provided by
    # InheritanceManager to allow traversal to the child model
    permission_children = PermissionableObject.objects.filter(
        permission_ancestors__ancestor_object=po_subclass_instance
        ).exclude(id=po_subclass_instance.id).select_subclasses()

    for child in permission_children:
        update_permission_ancestor_data(child, False)

