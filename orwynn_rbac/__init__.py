from orwynn import sql
from orwynn.base.module import Module

from orwynn_rbac.controllers import RolesController, RolesIdController
from orwynn_rbac.documents import Permission, Role
from orwynn_rbac.models import Action
from orwynn_rbac.mongo_state_flag import MongoStateFlagService
from orwynn_rbac.mongo_state_flag import module as mongo_state_flag_module
from orwynn_rbac.services import PermissionService, RoleService

__all__ = [
    "Permission",
    "Action",
]

module = Module(
    route="/",
    Providers=[
        PermissionService, RoleService
    ],
    Controllers=[RolesController, RolesIdController],
    imports=[sql.module, mongo_state_flag_module],
    exports=[PermissionService, RoleService],
)
