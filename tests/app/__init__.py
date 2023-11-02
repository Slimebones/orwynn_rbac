import asyncio
from typing import Callable

from orwynn.base import Module
from orwynn.boot import Boot
from orwynn.bootscript import Bootscript
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
from orwynn_rbac.services import AccessService
from tests.app.runner import run_server

DefaultRoles: list[DefaultRole] = [
    DefaultRole(
        name="master",
        title="Dungeon Master",
        permission_names=[
            "get:dungeons",
            "create:dungeons"
        ]
    ),
    DefaultRole(
        name="master",
        title="Dungeon Master",
        permission_names=[
            "get:dungeons",
            "create:dungeons"
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
        )
    ]
    Permissions = {
        "get": "get:dungeons",
        "post": "create:dungeons"
    }

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
        if user_id is None:
            raise ValueError
        self.service.check_user(user_id, str(request.url), request.method)

        response: HttpResponse = await call_next(request)

        return response


def create_root_module() -> Module:
    return Module(
        "/",
        Providers=[],
        Controllers=[DungeonsController],
        imports=[rbac_module]
    )


async def create_boot() -> Boot:
    return await Boot.create(
        create_root_module(),
        bootscripts=[
            RBACBoot(default_roles=DefaultRoles).get_bootscript()
        ],
        global_middleware={
            AccessMiddleware: ["*"],
        },
    )


async def main() -> None:
    await run_server(await create_boot())


if __name__ == "__main__":
    asyncio.run(main())
