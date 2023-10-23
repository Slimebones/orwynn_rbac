from typing import TYPE_CHECKING, Any, Iterable
from antievil import NotFoundError
from orwynn.app import AppMode
from orwynn.base.controller import Controller
from orwynn.mongo import MongoUtils
from orwynn.utils import validation
from sqlalchemy import select

from orwynn.base.service import Service
from orwynn.helpers.web import RequestMethod
from orwynn.log import Log
from orwynn.proxy.boot import BootProxy
from orwynn.sql import SQL
from orwynn_rbac.dtos import RoleUDto, RoleCDTO
from orwynn_rbac.errors import ActionAlreadyDefinedPermissionError, NoActionsForPermissionError, NonDynamicPermissionError, UnusedPermissionError
from orwynn_rbac.constants import DynamicPermissionNames
from orwynn_rbac.models import Action, DefaultRole, RoleCreate
from orwynn_rbac.search import PermissionSearch, RoleSearch
from orwynn_rbac.utils import NamingUtils, PermissionUtils
from orwynn_rbac.enums import PermissionDeletionReason
from orwynn_rbac.documents import Permission
from orwynn_rbac.documents import Role

if TYPE_CHECKING:
    from collections.abc import Sequence
    from orwynn_rbac.documents import Permission


class PermissionService(Service):
    """
    Manages permissions.
    """
    # Roles are managed with sql table, permissions and actions at runtime.

    def __init__(self) -> None:
        self._log = Log

    def get(
        self,
        search: PermissionSearch
    ) -> list[Permission]:
        query: dict[str, Any] = {}

        if search.ids:
            query["ids"] = {
                "$in": search.ids
            }
        if search.names:
            query["names"] = {
                "$in": search.names
            }
        if search.actions:
            converted_actions: list[dict[str, Any]] = []
            for action in search.actions:
                converted_actions.append({
                    "route": action.route,
                    "method": action.method.value
                })

            query["actions"] = {
                "$all": converted_actions
            }
        if search.is_dynamic:
            query["is_dynamic"] = search.is_dynamic

        return MongoUtils.process_query(
            query,
            search,
            Permission
        )

    def init(
        self,
        *,
        controllers: list[Controller],
    ) -> set[str]:
        """
        Initializes permissions and their actions for the system.

        Every controller can specify class-attribute `Permissions`. If this
        attribute is None/Unbound, it will be considered as only for authorized
        users ("user" role). The same consideration will be taken into account
        if target method does not exist in such attribute.

        All unused permissions are deleted.

        Returns:
            Set of permission ids affected in initialization.
        """
        affected_ids: set[str] = set()

        affected_ids.update(self._create_dynamic_or_skip())
        affected_ids.update(self._create_for_controllers(controllers))

        self._delete_unused(affected_ids)

        return affected_ids

    def _delete_unused(
        self,
        affected_ids: set[str]
    ) -> None:
        permissions: Iterable[Permission] = Permission.get({
            "id": {
                "$nin": list(affected_ids)
            }
        })

        for permission in permissions:
            permission.remove()

    def _create_dynamic_or_skip(
        self
    ) -> set[str]:
        """
        Creates dynamic permissions if these do not exist yet.
        """
        affected_ids: set[str] = set()

        for name in DynamicPermissionNames:
            affected_ids.add(self._create_one_or_overwrite(
                name=name,
                actions=None
            ).getid())

        return affected_ids

    def _create_for_controllers(
        self,
        controllers: list[Controller]
    ) -> set[str]:
        affected_ids: set[str] = set()

        for controller in controllers:
            controller_permissions: dict[str, str] | None = getattr(
                controller, "Permissions"
            )

            if controller_permissions is None:
                continue

            for method_str, permission_name in controller_permissions.items():
                validation.validate(method_str, str)
                validation.validate(permission_name, str)

                method: RequestMethod = RequestMethod(method_str)

                # register all controller route in a separate action
                actions: list[Action] = []
                for final_route in controller.final_routes:
                    actions.append(Action(
                        route=final_route,
                        method=method
                    ))

                affected_ids.add(self._create_one_or_overwrite(
                    name=permission_name,
                    actions=actions
                ).getid())

        return affected_ids

    def _create_one_or_overwrite(
        self,
        *,
        name: str,
        actions: list[Action] | None
    ) -> Permission:
        """
        Saves a permission in the system with given actions, or overwrites
        all actions for an existing one.

        Action can be None only if the permission associated with the
        given name is dynamic, otherwise NotDynamicForActionPermissionError
        is raised.
        """
        permission: Permission

        if actions is None and not NamingUtils.has_dynamic_prefix(name):
            raise NonDynamicPermissionError(
                permission_name=name,
                in_order_to="create without actions"
            )

        try:
            permission = self.get(PermissionSearch(names=[name]))[0]
        except NotFoundError:
            permission = Permission(
                name=name,
                actions=actions,
                is_dynamic=actions is None
            ).create()
        else:
            permission = permission.update(set={
                "actions": actions
            })

        return permission


class RoleService(Service):
    """
    Manages roles.
    """
    def __init__(
        self,
        permission_service: PermissionService,
    ) -> None:
        super().__init__()
        self._permission_service: PermissionService = permission_service

    def get(
        self,
        search: RoleSearch
    ) -> list[Role]:
        query: dict[str, Any] = {}

        if search.ids:
            query["ids"] = {
                "$in": search.ids
            }
        if search.names:
            query["names"] = {
                "$in": search.names
            }
        if search.permissions_ids:
            query["permissions_ids"] = {
                "$in": search.permissions_ids
            }
        if search.user_ids:
            query["user_ids"] = {
                "$in": search.user_ids
            }
        if search.is_dynamic:
            query["is_dynamic"] = search.is_dynamic

        return MongoUtils.process_query(
            query,
            search,
            Role
        )

    def get_dtos(
        self,
        search: RoleSearch
    ) -> RoleCDTO:
        roles: list[Role] = self.get(search)

        return RoleCDTO.convert(roles, self.convert_one_to_dto)

    def create(
        self,
        data: list[RoleCreate]
    ) -> list[Role]:
        """
        Creates a role.
        """
        roles: list[Role] = []

        for d in data:
            permissions: list[Permission] = self._permission_service.get(
                PermissionSearch(
                    ids=d.permission_ids
                )
            )

            roles.append(Role(
                name=d.name,
                title=d.title,
                description=d.description,
                permission_ids=d.permission_ids,
                is_dynamic=NamingUtils.has_dynamic_prefix(d.name)
            ).create())

        return roles

    def init_default_or_skip(
        self,
        default_roles: list[DefaultRole]
    ) -> list[Role]:
        """
        Initializes default set of roles to the system.

        Should be called after initialization of all permissions.

        Args:
            default_roles:
                List of default roles to initialize.
        """
        roles: list[Role] = []

        for default_role in default_roles:
            permission_ids: list[str] = [
                p.getid() for p in self._permission_service.get(
                    PermissionSearch(
                        names=default_role.permission_names
                    )
                )
            ]

            if len(permission_ids) != len(default_role.permission_names):
                raise NotFoundError(
                    title=\
                        "some/all permissions for default role permission"
                        " names",
                    value=default_role.permission_names,
                    options={
                        "default_role_name": default_role.name
                    }
                )

            roles.append(self.create([RoleCreate(
                name=default_role.name,
                title=default_role.title,
                description=default_role.description,
                permission_ids=permission_ids
            )])[0])

        return roles

    def convert_one_to_dto(
        self,
        role: Role,
    ) -> RoleUDto:
        return RoleUDto(
            id=role.getid(),
            name=role.name,
            title=role.title,
            description=role.description,
            permission_ids=role.permission_ids,
            user_ids=role.user_ids,
        )

    # TODO(ryzhovalex): move these checks to a role service
    #
    # @name.setter
    # def name(self, value: str):
    #     self._check_dynamic_rules(name=value, is_dynamic=self.is_dynamic)
    #     self._name = value

    # @staticmethod
    # def _check_dynamic_rules(*, name: str, is_dynamic: bool) -> None:
    #     _has_dynamic_prefix: bool = has_dynamic_prefix(name)

    #     if is_dynamic is True and not _has_dynamic_prefix:
    #         raise RequiredDynamicPrefixError(
    #             name=name,
    #         )
    #     elif is_dynamic is False and _has_dynamic_prefix:
    #         raise RestrictedDynamicPrefixError(
    #             name=name,
    #         )
