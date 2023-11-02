from fastapi import Query
from orwynn.http import Endpoint, EndpointResponse, HttpController

from orwynn_rbac.dtos import RoleCDTO, RoleUDTO
from orwynn_rbac.models import RoleCreateMany
from orwynn_rbac.search import RoleSearch
from orwynn_rbac.services import RoleService
from orwynn_rbac.utils import BaseUpdateOperator, UpdateOperator


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
        "get": "get:roles",
        "post": "create:roles",
        "delete": "delete:roles"
    }

    def __init__(
        self,
        sv: RoleService,
    ) -> None:
        super().__init__()
        self._sv: RoleService = sv

    def get(
        self,
        names: list[str] | None = Query(None),
    ) -> dict:
        return self._sv.get_cdto(RoleSearch(names=names)).api

    def post(
        self,
        data: RoleCreateMany
    ) -> dict:
        return self._sv.create_cdto(data.arr).api

    def delete(
        self,
        names: list[str] | None = Query(None)
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
        "get": "get:role",
        "patch": "update:role",
        "delete": "delete:role"
    }

    def __init__(
        self,
        sv: RoleService
    ) -> None:
        super().__init__()
        self._sv = sv

    def get(self, id: str) -> dict:
        return self._sv.get_udto(id).api

    def delete(self, id: str) -> dict:
        return self._sv.delete_udto(id).api

    def patch(self, id: str, base_update_operator: BaseUpdateOperator) -> dict:
        return self._sv.patch_one_udto(
            UpdateOperator.from_base(id, base_update_operator)
        ).api
