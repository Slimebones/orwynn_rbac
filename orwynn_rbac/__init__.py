from orwynn import sql
from orwynn.base.module import Module

from orwynn_rbac.documents import Permission
from orwynn_rbac.models import Action
from orwynn_rbac.mongo_state_flag import module as mongo_state_flag_module
from orwynn_rbac.services import PermissionService
from orwynn_rbac.controllers import RolesController
from orwynn_rbac.default import DefaultRole
from orwynn_rbac.services import RoleDtoRepo
from orwynn_rbac.controllers import RolesIdController
from orwynn_rbac.services import RoleRepo
from orwynn_rbac.documents import Role

__all__ = [
    "Permission",
    "Action",
]

module = Module(
    route="/",
    Providers=[PermissionService, RoleRepo, RoleDtoRepo],
    Controllers=[RolesController, RolesIdController],
    imports=[sql.module, mongo_state_flag_module],
    exports=[PermissionService, RoleRepo],
)
