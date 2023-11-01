from typing import Any, Iterable

from antievil import (
    AlreadyEventError,
    ForbiddenResourceError,
    LogicError,
    NotFoundError,
)
from bson import ObjectId
from orwynn.base.controller import Controller
from orwynn.base.service import Service
from orwynn.di.di import Di
from orwynn.log import Log
from orwynn.mongo import MongoUtils
from orwynn.utils import validation
from orwynn.utils.func import FuncSpec

from orwynn_rbac.constants import DynamicPermissionNames
from orwynn_rbac.documents import Permission, Role
from orwynn_rbac.dtos import RoleCDTO, RoleUDTO
from orwynn_rbac.errors import NonDynamicPermissionError
from orwynn_rbac.models import Action, DefaultRole, RoleCreate
from orwynn_rbac.search import PermissionSearch, RoleSearch
from orwynn_rbac.types import ControllerPermissions
from orwynn_rbac.utils import NamingUtils, PermissionUtils, UpdateOperator


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
            query["id"] = {
                "$in": search.ids
            }
        if search.names:
            query["name"] = {
                "$in": search.names
            }
        if search.actions:
            converted_actions: list[dict[str, Any]] = []
            for action in search.actions:
                converted_actions.append({
                    "controller_no": action.controller_no,
                    "method": action.method
                })

            query["actions"] = {
                "$in": converted_actions
            }
        if search.is_dynamic:
            query["is_dynamic"] = search.is_dynamic

        return MongoUtils.process_query(
            query,
            search,
            Permission
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
        affected_ids: set[str]
    ) -> set[str]:
        ids: set[str] = set()

        permissions: Iterable[Permission] = Permission.get({
            "id": {
                "$nin": list(affected_ids)
            }
        })

        for permission in permissions:
            ids.add(permission.getid())
            permission.remove()

        return ids

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
                pure_actions=None
            ).getid())

        return affected_ids

    def _create_for_controllers(
        self,
        controllers: list[Controller]
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
                        MongoUtils.convert_compatible(Action(
                            controller_no=controller_no,
                            method=method
                        )),
                        dict
                    )
                )

        for permission_name, actions \
                in pure_actions_by_permission_name.items():
            affected_ids.add(self._create_one_or_overwrite(
                name=permission_name,
                pure_actions=actions
            ).getid())

        return affected_ids

    def _create_one_or_overwrite(
        self,
        *,
        name: str,
        pure_actions: list[dict] | None
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
                in_order_to="create without actions"
            )

        try:
            permission = self.get(PermissionSearch(names=[name]))[0]
        except NotFoundError:
            permission = Permission(
                name=name,
                actions=pure_actions,
                is_dynamic=pure_actions is None
            ).create()
        else:
            permission = permission.update(set={
                "actions": pure_actions
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
            query["id"] = {
                "$in": search.ids
            }
        if search.names:
            query["name"] = {
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

    def get_udto(
        self,
        id: str
    ) -> RoleUDTO:
        return self.convert_one_to_udto(self.get(RoleSearch(ids=[id]))[0])

    def get_cdto(
        self,
        search: RoleSearch
    ) -> RoleCDTO:
        roles: list[Role] = self.get(search)

        return RoleCDTO.convert(roles, self.convert_one_to_udto)

    def set_for_user(
        self,
        user_id: str,
        search: RoleSearch
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
                    event=f"has a role {role}"
                )

            updates.append(
                FuncSpec(
                    fn=role.update,
                    kwargs={
                        "operators": {"$push": {"user_ids": user_id}}
                    }
                )
            )

        final_roles: list[Role] = []
        for u in updates:
            final_roles.append(u.call())

        if len(final_roles) != len(roles):
            err_message: str = \
                "unconsistent amount of input roles and final roles"
            raise LogicError(err_message)

        return final_roles

    def create(
        self,
        data: list[RoleCreate]
    ) -> list[Role]:
        """
        Creates a role.
        """
        roles: list[Role] = []

        for d in data:
            self._permission_service.get(
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

    def patch_one(
        self,
        update_operator: UpdateOperator
    ) -> Role:
        role: Role = self.get(RoleSearch(ids=[update_operator.id]))[0]

        query: dict[str, Any] = update_operator.get_mongo_update_query({
            "name": (str, ["$set"]),
            "title": (str, ["$set"]),
            "description": (str, ["$set"]),
            "permission_ids": (str, ["$push", "$pull"]),
            "user_ids": (str, ["$push", "$pull"])
        })

        # TODO(ryzhovalex):
        #   remove when Document.update start supporting
        #   direct query dict
        return role._parse_document(
            role._get_mongo().update_one(
                role._get_collection(),
                {"_id": ObjectId(role.getid())},
                query
            )
        )

    def patch_one_udto(
        self,
        update_operator: UpdateOperator
    ) -> RoleUDTO:
        return self.convert_one_to_udto(self.patch_one(update_operator))

    def _unlink_internal(
        self,
        permission_ids: list[str]
    ) -> None:
        """
        Unlinks deleted permissions from the according roles.
        """
        roles: list[Role] = self.get(RoleSearch(
            permissions_ids=permission_ids
        ))

        for r in roles:
            r.update(operators={
                "$pull": {
                    "permission_ids": {
                        "$in": permission_ids
                    }
                }
            })

    def _init_defaults_internal(
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
        permission_service: PermissionService
    ) -> None:
        super().__init__()

        self.role_service = role_service
        self.permission_service = permission_service

    def check_access(
        self,
        user_id: str | None,
        route: str,
        method: str
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

        permissions: list[Permission]
        if user_id is None:
            # check if the requested route allows for unauthorized users
            permissions = self.permission_service.get(PermissionSearch(
                ids=list(self.role_service.get(
                        RoleSearch(names=["dynamic:unauthorized"])
                    )[0].permission_ids)
            ))
        else:
            user_roles: list[Role] = self.role_service.get(
                RoleSearch(user_ids=[user_id])
            )

            permission_ids: set[str] = set()

            for role in user_roles:
                permission_ids.update(set(role.permission_ids))

            permissions = self.permission_service.get(PermissionSearch(
                ids=list(permission_ids)
            ))

        if not self._is_any_permission_matched(
            permissions,
            route,
            method,
            controllers
        ):
            raise ForbiddenResourceError(
                user=user_id,
                method=method,
                route=route
            )

    def _is_any_permission_matched(
        self,
        permissions: list[Permission],
        route: str,
        method: str,
        controllers: list[Controller]
    ) -> bool:
        for p in permissions:
            # no actions registerd => no access
            if not p.actions:
                return False

            for a in p.actions:
                target_controller: Controller = controllers[a.controller_no]

                if (
                    a.method.lower() == method.lower()
                    and target_controller.is_matching_route(route)
                ):
                    return True

        return False

