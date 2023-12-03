from orwynn import mongo
from orwynn.base.module import Module

from orwynn_rbac.controllers import (
    PermissionsController,
    RolesController,
    RolesIDController,
)
from orwynn_rbac.documents import Permission, Role
from orwynn_rbac.models import HTTPAction
from orwynn_rbac.services import AccessService, PermissionService, RoleService

__all__ = [
    "Permission",
    "HTTPAction",
    "Role",
    "PermissionService",
    "AccessService",
    "RoleService",
]

module = Module(
    route="/rbac",
    Providers=[
        PermissionService, RoleService, AccessService,
    ],
    Controllers=[RolesController, RolesIDController, PermissionsController],
    imports=[mongo.module],
    exports=[PermissionService, RoleService, AccessService],
)
