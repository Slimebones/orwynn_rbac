import contextlib
from typing import TYPE_CHECKING, Any, Iterable

from bson import ObjectId
from orwynn.base.controller import Controller
from orwynn.base.service import Service
from orwynn.di.di import Di
from orwynn.log import Log
from orwynn.mongo import MongoUtils
from pykit import validation
from pykit.errors import (
    AlreadyEventError,
    ForbiddenResourceError,
    LengthExpectError,
    LogicError,
    NotFoundError,
)
from pykit.func import FuncSpec

from orwynn_rbac.constants import DynamicPermissionNames
from orwynn_rbac.documents import Permission, Role
from orwynn_rbac.dtos import PermissionCDTO, PermissionUDTO, RoleCDTO, RoleUDTO
from orwynn_rbac.errors import NonDynamicPermissionError
from orwynn_rbac.models import DefaultRole, HTTPAction, RoleCreate
from orwynn_rbac.search import PermissionSearch, RoleSearch
from orwynn_rbac.utils import NamingUtils, PermissionUtils, UpdateOperator

if TYPE_CHECKING:
    from orwynn_rbac.types import ControllerPermissions


class PermissionService(Service):
    """
    Manages permissions.
    """
    # Roles are managed with a sql table, permissions and actions at runtime.

    def __init__(self) -> None:
        self._log = Log

    def get(
        self,
        search: PermissionSearch,
    ) -> list[Permission]:
        query: dict[str, Any] = {}

        if search.ids is not None:
            query["id"] = {
                "$in": search.ids,
            }
        if search.names is not None:
            query["name"] = {
                "$in": search.names,
            }
        if search.actions is not None:
            converted_actions: list[dict[str, Any]] = [
                {
                    "controller_no": action.controller_no,
                    "method": action.method,
                } for action in search.actions
            ]

            query["actions"] = {
                "$in": converted_actions,
            }
        if search.is_dynamic:
            query["is_dynamic"] = search.is_dynamic

        return MongoUtils.process_query(
            query,
            search,
            Permission,
        )

    def get_cdto(self, search: PermissionSearch) -> PermissionCDTO:
        return PermissionCDTO.convert(
            self.get(search),
            self.convert_one_to_udto,
        )

    def convert_one_to_udto(self, p: Permission) -> PermissionUDTO:
        return PermissionUDTO(
            id=p.getid(),
            name=p.name,
            actions=p.actions if p.actions else [],
            is_dynamic=p.is_dynamic,
        )

    def _init_internal(
        self,
        *,
        controllers: list[Controller],
    ) -> tuple[set[str], set[str]]:
        """
        Initializes permissions and their actions for the system.

        Every controller can specify class-attribute `Permissions`. If this
        attribute is None/Unbound, it will be considered as only for authorized
        users ("user" role). The same consideration will be taken into account
        if target method does not exist in such attribute.

        All unused permissions are deleted.

        Returns:
            Set of permission ids affected in initialization and set of
            permissions ids deleted during the initialization.
        """
        affected_ids: set[str] = set()

        affected_ids.update(self._create_dynamic_or_skip())
        affected_ids.update(self._create_for_controllers(controllers))

        deleted_ids: set[str] = self._delete_unused(affected_ids)

        return affected_ids, deleted_ids

    def _delete_unused(
        self,
        affected_ids: set[str],
    ) -> set[str]:
        ids: set[str] = set()

        permissions: Iterable[Permission] = Permission.get({
            "id": {
                "$nin": list(affected_ids),
            },
        })

        for permission in permissions:
            ids.add(permission.getid())
            permission.remove()

        return ids

    def _create_dynamic_or_skip(
        self,
    ) -> set[str]:
        """
        Creates dynamic permissions if these do not exist yet.
        """
        affected_ids: set[str] = set()

        for name in DynamicPermissionNames:
            affected_ids.add(self._create_one_or_overwrite(
                name=name,
                pure_actions=None,
            ).getid())

        return affected_ids

    def _create_for_controllers(
        self,
        controllers: list[Controller],
    ) -> set[str]:
        affected_ids: set[str] = set()
        pure_actions_by_permission_name: dict[str, list[dict]] = {}

        # controllers are numbered exactly as they are placed in DI's generated
        # array. It is not entirely safe, but it is a solution for now
        for controller_no, controller in enumerate(controllers):
            try:
                controller_permissions: ControllerPermissions = \
                    PermissionUtils.collect_controller_permissions(controller)
            except NotFoundError:
                continue

            for method, permission_name in controller_permissions.items():
                validation.validate(method, str)
                validation.validate(permission_name, str)

                # register all controller route in a separate action
                if permission_name not in pure_actions_by_permission_name:
                    pure_actions_by_permission_name[permission_name] = []
                pure_actions_by_permission_name[permission_name].append(
                    validation.apply(
                        MongoUtils.convert_compatible(HTTPAction(
                            controller_no=controller_no,
                            method=method,
                        )),
                        dict,
                    ),
                )

        for permission_name, actions \
                in pure_actions_by_permission_name.items():
            affected_ids.add(self._create_one_or_overwrite(
                name=permission_name,
                pure_actions=actions,
            ).getid())

        return affected_ids

    def _create_one_or_overwrite(
        self,
        *,
        name: str,
        pure_actions: list[dict] | None,
    ) -> Permission:
        """
        Saves a permission in the system with given actions, or overwrites
        all actions for an existing one.

        Action can be None only if the permission associated with the
        given name is dynamic, otherwise NotDynamicForActionPermissionError
        is raised.
        """
        permission: Permission

        if pure_actions is None and not NamingUtils.has_dynamic_prefix(name):
            raise NonDynamicPermissionError(
                permission_name=name,
                in_order_to="create without actions",
            )

        try:
            permission = self.get(PermissionSearch(names=[name]))[0]
        except NotFoundError:
            permission = Permission(
                name=name,
                actions=pure_actions,
                is_dynamic=pure_actions is None,
            ).create()
        else:
            permission = permission.update(set={
                "actions": pure_actions,
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
        search: RoleSearch,
    ) -> list[Role]:
        query: dict[str, Any] = {}

        if search.ids is not None:
            query["id"] = {
                "$in": search.ids,
            }
        if search.names is not None:
            query["name"] = {
                "$in": search.names,
            }
        if search.permission_ids is not None:
            query["permission_ids"] = {
                "$in": search.permission_ids,
            }
        if search.user_ids is not None:
            query["user_ids"] = {
                "$in": search.user_ids,
            }
        if search.is_dynamic:
            query["is_dynamic"] = search.is_dynamic

        return MongoUtils.process_query(
            query,
            search,
            Role,
        )

    def get_udto(
        self,
        id: str,
    ) -> RoleUDTO:
        return self.convert_one_to_udto(self.get(RoleSearch(ids=[id]))[0])

    def get_cdto(
        self,
        search: RoleSearch,
    ) -> RoleCDTO:
        roles: list[Role] = self.get(search)

        return RoleCDTO.convert(roles, self.convert_one_to_udto)

    def set_for_user(
        self,
        user_id: str,
        search: RoleSearch,
    ) -> list[Role]:
        """
        Finds all roles and sets them for an user id.

        Returns:
            List of roles set for an user.

        Raises:
            AlreadyEventError:
                Affected user already has some of the specified roles.
        """
        roles: list[Role] = self.get(search)
        updates: list[FuncSpec] = []

        for role in roles:
            if user_id in role.user_ids:
                raise AlreadyEventError(
                    title="user with id",
                    value=user_id,
                    event=f"has a role {role}",
                )

            updates.append(
                FuncSpec(
                    fn=role.update,
                    kwargs={
                        "operators": {"$push": {"user_ids": user_id}},
                    },
                ),
            )

        final_roles: list[Role] = [
            u.call() for u in updates
        ]

        if len(final_roles) != len(roles):
            err_message: str = \
                "unconsistent amount of input roles and final roles"
            raise LogicError(err_message)

        return final_roles

    def create(
        self,
        data: list[RoleCreate],
    ) -> list[Role]:
        """
        Creates a role.
        """
        roles: list[Role] = []

        for d in data:
            permissions: list[Permission] = []
            with contextlib.suppress(NotFoundError):
                permissions = self._permission_service.get(
                    PermissionSearch(
                        ids=d.permission_ids,
                    ),
                )

            permission_ids_len: int = \
                len(d.permission_ids) if d.permission_ids else 0
            if len(permissions) != permission_ids_len:
                raise LengthExpectError(
                    permissions,
                    permission_ids_len,
                    actual_length=len(permissions),
                )

            roles.append(Role(
                name=d.name,
                title=d.title,
                description=d.description,
                permission_ids=[p.getid() for p in permissions],
                is_dynamic=NamingUtils.has_dynamic_prefix(d.name),
            ).create())

        return roles

    def create_cdto(
        self,
        data: list[RoleCreate],
    ) -> RoleCDTO:
        return RoleCDTO.convert(self.create(data), self.convert_one_to_udto)

    def delete(
        self,
        search: RoleSearch,
    ) -> list[Role]:
        roles: list[Role] = self.get(search)

        for role in roles:
            role.remove()

        return roles

    def delete_udto(
        self,
        id: str,
    ) -> RoleUDTO:
        return self.convert_one_to_udto(self.delete(RoleSearch(ids=[id]))[0])

    def delete_cdto(
        self,
        search: RoleSearch,
    ) -> RoleCDTO:
        return RoleCDTO.convert(self.delete(search), self.convert_one_to_udto)

    def patch_one(
        self,
        update_operator: UpdateOperator,
    ) -> Role:
        role: Role = self.get(RoleSearch(ids=[update_operator.id]))[0]

        query: dict[str, Any] = update_operator.get_mongo_update_query({
            "name": (str, ["$set"]),
            "title": (str, ["$set"]),
            "description": (str, ["$set"]),
            "permission_ids": (str, ["$push", "$pull"]),
            "user_ids": (str, ["$push", "$pull"]),
        })

        # TODO(ryzhovalex):
        #   remove when Document.update start supporting
        #   direct query dict
        return role._parse_document(  # noqa: SLF001
            role._get_mongo().update_one(  # noqa: SLF001
                role._get_collection(),  # noqa: SLF001
                {"_id": ObjectId(role.getid())},
                query,
            ),
        )

    def patch_one_udto(
        self,
        update_operator: UpdateOperator,
    ) -> RoleUDTO:
        return self.convert_one_to_udto(self.patch_one(update_operator))

    def _unlink_internal(
        self,
        permission_ids: list[str],
    ) -> None:
        """
        Unlinks deleted permissions from the according roles.
        """
        try:
            roles: list[Role] = self.get(RoleSearch(
                permission_ids=permission_ids,
            ))
        except NotFoundError:
            Log.info("[orwynn_rbac] no permissions to unlink from roles")
            return

        for r in roles:
            r.update(operators={
                "$pull": {
                    "permission_ids": {
                        "$in": permission_ids,
                    },
                },
            })

    def _init_defaults_internal(
        self,
        default_roles: list[DefaultRole],
        unauthorized_user_permissions: list[str] | None = None,
        authorized_user_permissions: list[str] | None = None,
    ) -> list[Role]:
        """
        Initializes default set of roles to the system.

        Should be called after initialization of all permissions.

        Args:
            default_roles:
                List of default roles to initialize.
        """
        roles: list[Role] = []

        final_default_roles: list[DefaultRole] = [
            DefaultRole(
                name="dynamic:unauthorized",
                title="Unauthorized",
                permission_names=
                    unauthorized_user_permissions
                        if unauthorized_user_permissions else [],
            ),
            DefaultRole(
                name="dynamic:authorized",
                title="Authorized",
                permission_names=
                    authorized_user_permissions
                        if authorized_user_permissions else [],
            ),
        ]

        final_default_roles.extend(default_roles)

        for default_role in final_default_roles:
            default_role_permissions: list[Permission]
            try:
                default_role_permissions = self._permission_service.get(
                    PermissionSearch(
                        names=default_role.permission_names,
                    ),
                )
            except NotFoundError:
                default_role_permissions = []

            permission_ids: list[str] = [
                p.getid() for p in default_role_permissions
            ]

            if len(permission_ids) != len(default_role.permission_names):
                raise NotFoundError(
                    title=\
                        "some/all permissions for default role permission"
                        " names",
                    value=default_role.permission_names,
                    options={
                        "default_role_name": default_role.name,
                    },
                )

            roles.append(self.create([RoleCreate(
                name=default_role.name,
                title=default_role.title,
                description=default_role.description,
                permission_ids=permission_ids,
            )])[0])

        return roles

    def convert_one_to_udto(
        self,
        role: Role,
    ) -> RoleUDTO:
        return RoleUDTO(
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


class AccessService(Service):
    """
    Checks if user has an access to action.
    """
    def __init__(
        self,
        role_service: RoleService,
        permission_service: PermissionService,
    ) -> None:
        super().__init__()

        self._role_service = role_service
        self._permission_service = permission_service

    def check_user(
        self,
        user_id: str | None,
        route: str,
        method: str,
    ) -> None:
        """
        Checks whether the user has an access to the route and method.

        If user id is None, it is considered that the request is made from an
        unauthorized client.

        Raises:
            ForbiddenError:
                User does not have an access.
        """
        controllers: list[Controller] = Di.ie().controllers

        permissions: list[Permission] = self._get_permissions_for_user_id(
            user_id,
        )

        # also pass empty permission list, since it can be an uncovered
        # controller where everyone is allowed
        if not self._is_any_permission_matched(
            permissions,
            route,
            method,
            controllers,
        ):
            raise ForbiddenResourceError(
                user=user_id,
                method=method,
                route=route,
            )

    def _get_unauthorized_permissions(self) -> list[Permission]:
        try:
            return self._permission_service.get(PermissionSearch(
                ids=list(self._role_service.get(
                    RoleSearch(names=["dynamic:unauthorized"]),
                )[0].permission_ids),
            ))
        except NotFoundError:
            return []

    def _get_permissions_for_user_id(
        self,
        user_id: str | None,
    ) -> list[Permission]:
        if user_id is None:
            # check if the requested route allows for unauthorized users
            return self._get_unauthorized_permissions()
        else:
            user_roles: list[Role] = []
            try:
                user_roles = self._role_service.get(
                    RoleSearch(user_ids=[user_id]),
                )
            except NotFoundError:
                # check if the requested route allows for authorized users
                # without any permissions
                try:
                    return self._permission_service.get(PermissionSearch(
                        ids=list(self._role_service.get(
                            RoleSearch(names=["dynamic:authorized"]),
                        )[0].permission_ids),
                    ))
                except NotFoundError:
                    return []

            permission_ids: set[str] = set()

            for role in user_roles:
                permission_ids.update(set(role.permission_ids))

            try:
                return self._permission_service.get(PermissionSearch(
                    ids=list(permission_ids),
                ))
            except NotFoundError:
                return []

    # TODO(ryzhovalex):
    #   replace this with HttpController.has_method when it comes out
    def _controller_has_method(self, c: Controller, method: str) -> bool:
        return getattr(c, method.lower(), None) is not None

    def _is_any_permission_matched(
        self,
        permissions: list[Permission],
        route: str,
        method: str,
        controllers: list[Controller],
    ) -> bool:
        # find matching controller
        for i, c in enumerate(controllers):
            if (
                c.is_matching_route(route)
                and self._controller_has_method(c, method)
            ):
                ControllerPermissions: dict[str, str] | None = getattr(
                    c, "Permissions", None,
                )

                if ControllerPermissions is None:
                    # controller without permissions is considered uncovered
                    return "dynamic:uncovered" in {p.name for p in permissions}

                try:
                    ControllerPermissions[method.lower()]
                except KeyError:
                    # such method is uncovered
                    return "dynamic:uncovered" in {p.name for p in permissions}


                # find matching permission for the controller
                for p in permissions:
                    if not p.actions:
                        continue

                    # TODO(ryzhovalex):
                    #   memorize supported controller numbers for this
                    #   permission set
                    for a in p.actions:
                        if (
                            a.controller_no == i
                            and method.lower() == a.method.lower()
                            and (
                                ControllerPermissions[a.method.lower()]
                                == p.name
                            )
                        ):
                            return True

                return False

        raise NotFoundError(
            title="no controllers found for route",
            value=route,
        )
