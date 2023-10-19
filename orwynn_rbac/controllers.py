from fastapi import Query
from orwynn.http import Endpoint, EndpointResponse, HttpController

from orwynn_rbac.dto import RoleDto, RolesDto
from orwynn_rbac.services import RoleDtoRepo


class RolesController(HttpController):
    ROUTE = "/roles"
    ENDPOINTS = [
        Endpoint(
            method="get",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=RolesDto,
                ),
            ],
        ),
    ]
    PERMISSIONS = {
        "get": "get:role",
    }

    def __init__(
        self,
        dto_repo: RoleDtoRepo,
    ) -> None:
        super().__init__()
        self._dto_repo: RoleDtoRepo = dto_repo

    async def get(
        self,
        names: list[str] | None = Query(None),
    ) -> dict:
        return self._dto_repo.get_all(names=names).api


class RolesIdController(HttpController):
    ROUTE = "/roles/{id}"
    ENDPOINTS = [
        Endpoint(
            method="get",
            tags=["rbac"],
            responses=[
                EndpointResponse(
                    status_code=200,
                    Entity=RoleDto,
                ),
            ],
        ),
    ]
    PERMISSIONS = {
        "get": "get:role",
    }

    def __init__(
        self,
        dto_repo: RoleDtoRepo,
    ) -> None:
        super().__init__()
        self._dto_repo: RoleDtoRepo = dto_repo

    def get(self, id: str) -> dict:
        return self._dto_repo.get_one(id).api
