from orwynn import mongo
from orwynn.base.module import Module

from orwynn_rbac.controllers import RolesController, RolesIDController
from orwynn_rbac.documents import Permission, Role
from orwynn_rbac.models import Action
from orwynn_rbac.services import AccessService, PermissionService, RoleService

__all__ = [
    "Permission",
    "Action",
    "Role",
    "PermissionService",
    "AccessService",
    "RoleService"
]

module = Module(
    route="/rbac",
    Providers=[
        PermissionService, RoleService, AccessService
    ],
    Controllers=[RolesController, RolesIDController],
    imports=[mongo.module],
    exports=[PermissionService, RoleService, AccessService],
)
