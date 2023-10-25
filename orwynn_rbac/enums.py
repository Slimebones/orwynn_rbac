from enum import Enum


class PermissionAbstractAction(Enum):
    """
    Possible set of actions can be defined in a permission name.

    Items:
        Create: to create something
        Get: to get something
        Update: to change something
        Delete: to delete something
        Do: other than CRUD actions to be performed
    """
    Create = "create"
    Get = "get"
    Update = "update"
    Delete = "delete"
    Do = "do"
