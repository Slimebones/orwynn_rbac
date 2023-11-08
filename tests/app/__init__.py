import asyncio
from typing import Callable

from orwynn.base import Module
from orwynn.boot import Boot
from orwynn.bootscript import Bootscript
from orwynn.di.di import Di
from orwynn.http import (
    Endpoint,
    EndpointResponse,
    HttpController,
    HttpMiddleware,
    HttpRequest,
    HttpResponse,
)

from orwynn_rbac import module as rbac_module
from orwynn_rbac.bootscripts import RBACBoot
from orwynn_rbac.models import DefaultRole
from orwynn_rbac.search import RoleSearch
from orwynn_rbac.services import AccessService, RoleService
from orwynn_rbac.utils import UpdateOperator
from tests.app.runner import run_server

DefaultRoles: list[DefaultRole] = [
    DefaultRole(
        name="master",
        title="Dungeon Master",
        permission_names=[
            "get:dungeons",
            "create:dungeons",
            "get:roles",
            "create:roles",
            "update:role",
            "delete:roles",
        ]
    ),
    DefaultRole(
        name="player",
        title="Player",
        permission_names=[
            "get:dungeons",
            "get:roles",
        ]
    ),
]


class DungeonsController(HttpController):
    Route = "/dungeons"
    Endpoints = [
        Endpoint(
            method="get"
        ),
        Endpoint(
            method="post"
        ),
        Endpoint(
            method="patch"
        ),
        Endpoint(
            method="put"
        )
    ]
    Permissions = {
        "get": "get:dungeons",
        "post": "create:dungeons",
        "patch": "update:dungeons"
    }

    def get(self) -> dict:
        return {"type": "ok"}

    def post(self) -> dict:
        return {"type": "ok"}

    def patch(self) -> dict:
        return {"type": "ok"}

    def put(self) -> dict:
        return {"type": "ok"}


class UncoveredController(HttpController):
    Route = "/uncovered"
    Endpoints = [
        Endpoint(
            method="get"
        ),
        Endpoint(
            method="post"
        )
    ]

    def get(self) -> dict:
        return {"type": "ok"}

    def post(self) -> dict:
        return {"type": "ok"}


class AccessMiddleware(HttpMiddleware):
    def __init__(
        self,
        covered_routes: list[str],
        service: AccessService,
    ) -> None:
        super().__init__(covered_routes)
        self.service: AccessService = service

    async def process(
        self,
        request: HttpRequest,
        call_next: Callable,
    ) -> HttpResponse:
        user_id: str | None = request.headers.get("user-id", None)
        self.service.check_user(
            user_id, str(request.url.components.path), request.method
        )

        response: HttpResponse = await call_next(request)

        return response


def create_root_module() -> Module:
    return Module(
        "/",
        Providers=[],
        Controllers=[DungeonsController, UncoveredController],
        imports=[rbac_module]
    )


async def create_boot() -> Boot:
    boot = await Boot.create(
        create_root_module(),
        bootscripts=[
            RBACBoot(
                default_roles=DefaultRoles,
                unauthorized_user_permissions=["get:dungeons"],
                authorized_user_permissions=["get:roles"]
            ).get_bootscript()
        ],
        global_middleware={
            AccessMiddleware: ["*"],
        },
    )

    # assign users to roles
    role_service: RoleService = Di.ie().find("RoleService")

    role = role_service.get(RoleSearch(names=["master"]))[0]
    role_service.patch_one(UpdateOperator(
        id=role.getid(),
        push={
            "user_ids": "1"
        }
    ))

    role = role_service.get(RoleSearch(names=["player"]))[0]
    role_service.patch_one(UpdateOperator(
        id=role.getid(),
        push={
            "user_ids": "2"
        }
    ))

    return boot


async def main() -> None:
    await run_server(await create_boot())


if __name__ == "__main__":
    asyncio.run(main())
