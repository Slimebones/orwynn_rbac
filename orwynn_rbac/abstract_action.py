from enum import Enum


class PermissionAbstractAction(Enum):
    """
    Possible set of actions can be defined in a permission name.

    Items:
        CREATE: to create something
        GET: to get something
        UPDATE: to change something
        DELETE: to delete something
        DO: other than CRUD actions to be performed
    """
    CREATE = "create"
    GET = "get"
    UPDATE = "update"
    DELETE = "delete"
    DO = "do"
