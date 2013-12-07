# Django object permissions

This application is inspired by the object permission system used in
the (now-legacy) OpenACS web platform. See e.g.:

http://openacs.org/doc/permissions.html

http://openacs.org/doc/permissions-tediously-explained.html

It is experimental at this point - NOT production-ready code.


## Core concepts: object-based permissions with context hierarchies

Although the implementation here is different from - and simpler
than - the one in OpenACS, it preserves key ideas and features:

* The systems assigns permissions to "parties" over generic,
"permissionable" objects. Parties can be individuals or groups.

* To incorporate parties and permissionable objects into an application
data model, the developer subtypes models provided in this
application: Party and PermissionableObject.

* All permission information can be derived from the data in a single,
three-column table - in this case the model PartyPrivilege. Each row
stores a party, a permissionable object, and a permission type.

* Permissions can be assigned and queried by simple, uniform functions
and methods (see below).

* Rather than trying to store and manage information about all
possible relationships between parties and permissionable objects, the
system makes use of hierarchical relationships within the
data. Parties can be organized into groups, or groups of
groups. Likewise, permissionable objects can inherit permissions from
parent objects.

The design here differs from the system found in OpenACS in some
important ways.

* OpenACS uses a single hierarchy of permissionable objects, rooted at
  the "security context root". Django object permissions derives
  hierarchies from the foreign keys of models that sub-class
  PermissionableObject. This means that single instance of
  PermissionableObject can belong to multiple hierarchies. (Note that
  inheritance only takes place for foreign keys that are flagged to
  create inherited permissions.)

* OpenACS denormalizes the hierarchies using auxiliary tables and
  database triggers. Django object permissions (for now) uses a simple
  system that generates not-so-simple queries. The scalability of this
  approach is questionable (see caveats, below).

* OpenACS provides for a hierarchy of permission types (e.g. "admin"
  is the parent permission of "read", "write", and "delete"). Django
  object permissions are (for now) flat.


## Caveats

Performance...


## Usage

To expose a model to the permissioning system, subclass
PermissionableObject.

```
from object_permissions.models import PermissionableObject

class MyModel(PermissionableObject):
      pass
```

To create models describing individuals or groups that are assigned
permissions, subclass Party.

```
from object_permissions.models import Party

class MyUser(Party):
      pass
```

TBD: Group membership.


To assign a given permission over a "permissionable" object:

```
from object_permissions.utils import assign_permission

some_object = MyModel.objects.get(id=somevar)
some_party = MyUser.objects.get(id=somevar)

assign_permission(some_object, some_party, 'admin')
```

To test for a given permission over an object:

```
from object_permissions.utils import has_permission

some_object = MyModel.objects.get(id=somevar)
some_party = MyUser.objects.get(id=somevar)

has_permission(some_object, some_party, 'admin')
```
 (This returns a boolean value.)


To get a queryset based on permissions, use the method
get_permitted_items on a model that inherits from
PermissionableObject.

```
MyModel.get_permitted_items(some_party, 'some_privilege')
```

The method returns a query set that can be further filtered.


To create inherited permissions between two related models, subclass
PermissionableObject for both models, and designate the foreign keys
for permission inheritance using the attribue
permission_parent_classes:

```
class W(PermissionableObject):
    name = models.CharField(max_length=100)

class X(PermissionableObject):
    permission_parent_classes = [W]
    name = models.CharField(max_length=100)
    w = models.ForeignKey(W)
````

In the example above, if we grant a party the permission "admin" over
an instance of W, that party will also have admin permissions on
related instances of X. Note that this system can traverse n foreign
key relationships.



