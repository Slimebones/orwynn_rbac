from fastapi import Query
from orwynn.http import Endpoint, EndpointResponse, HttpController

from orwynn_rbac.dtos import RoleCDTO, RoleUDTO
from orwynn_rbac.search import RoleSearch
from orwynn_rbac.services import RoleService


class RolesController(HttpController):
    ROUTE = "/roles"
    ENDPOINTS = [
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
    ]
    Permissions = {
        "get": "get:role",
    }

    def __init__(
        self,
        sv: RoleService,
    ) -> None:
        super().__init__()
        self._sv: RoleService = sv

    async def get(
        self,
        names: list[str] | None = Query(None),
    ) -> dict:
        return self._sv.get_cdto(RoleSearch(names=names)).api


class RolesIDController(HttpController):
    ROUTE = "/roles/{id}"
    ENDPOINTS = [
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
    ]
    Permissions = {
        "get": "get:role",
    }

    def __init__(
        self,
        sv: RoleService
    ) -> None:
        super().__init__()
        self._sv = sv

    def get(self, id: str) -> dict:
        return self._sv.get_udto(id).api
