from orwynn import mongo
from orwynn.base.module import Module

from orwynn_rbac import mongo_state_flag
from orwynn_rbac.controllers import RolesController, RolesIdController
from orwynn_rbac.documents import Permission, Role
from orwynn_rbac.models import Action
from orwynn_rbac.mongo_state_flag import MongoStateFlagService
from orwynn_rbac.services import PermissionService, RoleService

__all__ = [
    "Permission",
    "Action",
]

module = Module(
    route="/rbac",
    Providers=[
        PermissionService, RoleService
    ],
    Controllers=[RolesController, RolesIdController],
    imports=[mongo.module, mongo_state_flag.module],
    exports=[PermissionService, RoleService],
)
