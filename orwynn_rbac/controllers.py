from fastapi import Query
from orwynn.http import Endpoint, EndpointResponse, HttpController

from orwynn_rbac.dtos import PermissionCDTO, RoleCDTO, RoleUDTO
from orwynn_rbac.models import RoleCreateMany
from orwynn_rbac.search import PermissionSearch, RoleSearch
from orwynn_rbac.services import PermissionService, RoleService
from orwynn_rbac.utils import BaseUpdateOperator, UpdateOperator


class PermissionsController(HttpController):
    Route = "/permissions"
    Endpoints = [
        Endpoint(
            method="get",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=PermissionCDTO,
                ),
            ],
        ),
    ]
    Permissions = {
        "get": "slimebones.orwynn-rbac.permissions-permission:get",
    }

    def __init__(
        self,
        sv: PermissionService,
    ) -> None:
        super().__init__()
        self._sv: PermissionService = sv

    def get(
        self,
        ids: list[str] | None = Query(None),
        names: list[str] | None = Query(None),
    ) -> dict:
        return self._sv.get_cdto(PermissionSearch(ids=ids, names=names)).api


class RolesController(HttpController):
    Route = "/roles"
    Endpoints = [
        Endpoint(
            method="get",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=RoleCDTO,
                ),
            ],
        ),
        Endpoint(
            method="post",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=RoleCDTO,
                ),
            ],
        ),
        Endpoint(
            method="delete",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=RoleCDTO,
                ),
            ],
        ),
    ]
    Permissions = {
        "get": "slimebones.orwynn-rbac.roles-permission:get",
        "post": "slimebones.orwynn-rbac.roles-permission:create",
        "delete": "slimebones.orwynn-rbac.roles-permission:delete",
    }

    def __init__(
        self,
        sv: RoleService,
    ) -> None:
        super().__init__()
        self._sv: RoleService = sv

    def get(
        self,
        ids: list[str] | None = Query(None),
        names: list[str] | None = Query(None),
    ) -> dict:
        return self._sv.get_cdto(RoleSearch(ids=ids, names=names)).api

    def post(
        self,
        data: RoleCreateMany,
    ) -> dict:
        return self._sv.create_cdto(data.arr).api

    def delete(
        self,
        names: list[str] | None = Query(None),
    ) -> dict:
        return self._sv.delete_cdto(RoleSearch(names=names)).api


class RolesIDController(HttpController):
    Route = "/roles/{id}"
    Endpoints = [
        Endpoint(
            method="get",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=RoleUDTO,
                ),
            ],
        ),
        Endpoint(
            method="delete",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=RoleUDTO,
                ),
            ],
        ),
        Endpoint(
            method="patch",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=RoleUDTO,
                ),
            ],
        ),
    ]
    Permissions = {
        "get": "slimebones.orwynn-rbac.role-permission:get",
        "patch": "slimebones.orwynn-rbac.role-permission:update",
        "delete": "slimebones.orwynn-rbac.role-permission:delete",
    }

    def __init__(
        self,
        sv: RoleService,
    ) -> None:
        super().__init__()
        self._sv = sv

    def get(self, id: str) -> dict:
        return self._sv.get_udto(id).api

    def delete(self, id: str) -> dict:
        return self._sv.delete_udto(id).api

    def patch(self, id: str, base_update_operator: BaseUpdateOperator) -> dict:
        return self._sv.patch_one_udto(
            UpdateOperator.from_base(id, base_update_operator),
        ).api
