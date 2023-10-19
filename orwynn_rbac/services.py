from typing import TYPE_CHECKING, Any
from antievil import NotFoundError
from orwynn.app import AppMode
from orwynn.base.controller import Controller
from orwynn.mongo import MongoUtils
from sqlalchemy import select

from orwynn.base.service import Service
from orwynn.helpers.web import RequestMethod
from orwynn.log import Log
from orwynn.proxy.boot import BootProxy
from orwynn.sql import SQL
from orwynn_rbac.dto import RoleDto, RolesDto, Sql
from orwynn_rbac.errors import ActionAlreadyDefinedPermissionError, NoActionsForPermissionError, NotDynamicForActionPermissionError
from orwynn_rbac.constants import DynamicPermissionNames
from orwynn_rbac.models import Action
from orwynn_rbac.search import PermissionSearch
from orwynn_rbac.types import ControllerPermissions
from orwynn_rbac.utils import NamingUtils, PermissionUtils
from orwynn_rbac.enums import PermissionDeletionReason
from orwynn_rbac.documents import Permission
from orwynn_rbac.documents import Role

if TYPE_CHECKING:
    from collections.abc import Sequence
    from orwynn_rbac.documents import Permission

# TODO(ryzhovalex): move these checks to a service
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
        if search.role_ids:
            query["role_ids"] = {
                "$in": search.role_ids
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
    ) -> None:
        """
        Initializes permissions and their actions for the system.

        Every controller can specify class-attribute `Permissions`. If this
        attribute is None/Unbound, it will be considered as only for authorized
        users ("user" role). The same consideration will be taken into account
        if target method does not exist in such attribute.
        """

    def _create_dynamic(
        self
    ) -> list[str]:
        """
        Creates dynamic permissions if these do not exist yet.
        """

    def _create_or_overwrite(
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
            raise NotDynamicForActionPermissionError(
                permission_name=name,
                in_order_to="create without actions"
            )

        try:
            permission = self.get(PermissionSearch(names=[name]))[0]
        except NotFoundError:
            permission = Permission(name=name).create()

        if actions is not None:
            permission = permission.update(set={
                "actions": actions
            })

        return permission


class RoleRepo(Service):
    """
    Manages roles.
    """
    def __init__(
        self,
        sql: Sql,
        permission_service: PermissionService,
    ) -> None:
        super().__init__()

        self._sql: Sql = sql
        self._permission_service: PermissionService = permission_service

        self._memorized_default_roles: dict[str, DefaultRole] = {}

    def get_one(
        self,
        id: str,
        shd: usql.Shd,
    ) -> Role:
        return usql.get_one(
            id,
            Role,
            shd,
        )

    def get_all(
        self,
        shd: usql.Shd,
        *,
        ids: list[str] | None = None,
        names: list[str] | None = None,
    ) -> list[Role]:
        selection = shd.select(
            Role,
        )

        if type(ids) is list:
            selection = selection.where(
                Role.id.in_(ids),
            )
        if type(names) is list:
            selection = selection.where(
                Role.name.in_(names),  # type: ignore
            )

        result: Sequence[Role] | None = shd.scalars(selection).all()

        if not result:
            raise NotFoundError(
                title="roles",
                options={
                    "names": names,
                },
            )

        return list(result)

    def get_for_names(
        self,
        names: list[str],
        shd: usql.Shd,
    ) -> list[Role]:
        roles: list[Role] = \
            shd.query(Role).filter(Role._name.in_(names)).all()  # noqa: SLF001

        if roles == []:
            raise NotFoundError(
                title="roles",
                options={
                    "names": names,
                },
            )
        else:
            return roles

    def get_default(
        self,
        *,
        name: str,
    ) -> DefaultRole:
        if name in self._memorized_default_roles:
            return self._memorized_default_roles[name]
        else:
            for role in DEFAULT_ROLES:
                if role.name == name:
                    self._memorized_default_roles[name] = role
                    return role

        raise NotFoundError(
            title="default role with name",
            value=name,
        )

    def create(
        self,
        *,
        name: str,
        permission_names: list[str],
        title: str | None = None,
        description: str | None = None,
        shd: usql.Shd,
    ) -> Role:
        """
        Creates a role.
        """
        with Shd.inherit(shd) as shd:
            permissions: list[Permission] = \
                self._permission_service.get_all_by_names(
                    permission_names,
                    shd,
                )

            role: Role = Role(
                name=name,

                title=title,
                description=description,

                permissions=permissions,
                _is_dynamic=has_dynamic_prefix(name),
            )

            shd.add(role)

            return role


    def initialize_defaults(
        self,
        default_roles: list[DefaultRole] | None = None,
    ) -> None:
        """
        Initialized default set of roles to the system.

        Should be called after initialization of all permissions.

        Note that this action should not be repeated on already initialized
        database, or sql unique field errors will be raised.

        Args:
            default_roles(optional):
                List of default roles to initialize. If None, the hardcoded
                dictionary will be used. Defaults to None.
        """
        final_default_roles = \
            DEFAULT_ROLES if default_roles is None else default_roles

        for default_role in final_default_roles:
            with usql.Shd.new(self._sql) as shd:
                self.create(
                    shd=shd,
                    name=default_role.name,
                    title=default_role.title,
                    description=default_role.description,
                    permission_names=[
                        model.name
                        for model
                        in self._permission_service.get_models_by_names(
                            list(default_role.permission_names),
                        )
                    ],
                )
                shd.execute_final()


class RoleDtoRepo(Service):
    """
    Manages role dtos.
    """
    def __init__(
        self,
        sql: Sql,
        role_repo: RoleRepo,
    ) -> None:
        super().__init__()

        self._sql: Sql = sql
        self._role_repo: RoleRepo = role_repo

    def get_one(
        self,
        id: str,
        shd: usql.Shd | None = None,
    ) -> RoleDto:
        with usql.Shd(self._sql, shd) as shd:
            return self.convert_one(self._role_repo.get_one(
                id,
                shd,
            ))

    def get_all(
        self,
        *,
        names: list[str] | None = None,
    ) -> RolesDto:
        with usql.Shd.new(self._sql) as shd:
            return RolesDto.convert(
                self._role_repo.get_all(
                    shd,
                    names=names,
                ),
                self.convert_one,
            )

    def convert_one(
        self,
        role: Role,
    ) -> RoleDto:
        return RoleDto(
            id=role.id,
            name=role.name,
            title=role.title,
            description=role.description,
            permission_ids=[p.id for p in role.permissions],
            user_ids=[u.id for u in role.users],
        )
