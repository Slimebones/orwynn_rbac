import os
from collections.abc import Callable
from typing import TYPE_CHECKING, AsyncGenerator

import pytest
import pytest_asyncio
from orwynn.app import App
from orwynn.base import Module, Worker
from orwynn.boot import Boot
from orwynn.di.di import Di
from orwynn.http import (
    Endpoint,
    HttpController,
    HttpMiddleware,
    HttpRequest,
    HttpResponse,
)
from orwynn.mongo import Mongo
from orwynn.mongo import module as mongo_module
from orwynn.testing import Client
from pykit import validation

from orwynn_rbac import module as rbac_module
from orwynn_rbac.bootscripts import RBACBoot
from orwynn_rbac.models import DefaultRole, RoleCreate
from orwynn_rbac.search import PermissionSearch, RoleSearch
from orwynn_rbac.services import AccessService, PermissionService, RoleService

if TYPE_CHECKING:
    from starlette.datastructures import Headers

DefaultRoles: list[DefaultRole] = [
    DefaultRole(
        name="ceo",
        title="Shop CEO",
        description="He is a true boss!",
        permission_names=[
            "slimebones.orwynn-rbac.testing.item-permission:get",
            "slimebones.orwynn-rbac.permissions-permission:get",
            "slimebones.orwynn-rbac.testing.item-permission:update",
            "slimebones.orwynn-rbac.testing.buy-item-permission:do",
            "slimebones.orwynn-rbac.role-permission:get",
            "slimebones.orwynn-rbac.roles-permission:get",
            "slimebones.orwynn-rbac.roles-permission:create",
            "slimebones.orwynn-rbac.role-permission:update",
            "slimebones.orwynn-rbac.role-permission:delete",
            "slimebones.orwynn-rbac.roles-permission:delete",
        ],
    ),
    DefaultRole(
        name="guard",
        title="Shop Guard",
        description="You will not pass!",
        permission_names=[
            "slimebones.orwynn-rbac.testing.item-permission:get",
        ],
    ),
]


class AccessMiddleware(HttpMiddleware):
    def __init__(
        self,
        covered_routes: list[str],
        role_service: RoleService,
        permission_service: PermissionService,
        access_service: AccessService,
    ) -> None:
        super().__init__(covered_routes)

        self.role_service = role_service
        self.permission_service = permission_service
        self.access_service = access_service

    async def process(
        self,
        request: HttpRequest,
        call_next: Callable,
    ) -> HttpResponse:
        headers: Headers = request.headers

        user_id: str | None = headers.get("user-id", None)

        method: str = request.method
        route: str = request.url.path

        self.access_service.check_user(user_id, route, method)

        response: HttpResponse = await call_next(request)

        return response


class ItemsController(HttpController):
    Route = "/items"
    Endpoints = [
        Endpoint(method="get"),
    ]
    Permissions = {
        "get": "slimebones.orwynn-rbac.testing.item-permission:get",
    }

    def get(self) -> dict:
        return {"item": "all"}


class ItemsIDController(HttpController):
    Route = "/items/{id}"
    Endpoints = [
        Endpoint(method="get"),
    ]
    Permissions = {
        "patch": "slimebones.orwynn-rbac.testing.item-permission:update",
    }

    def patch(self, id: str) -> dict:
        return {"item": id}


class ItemsIDBuyController(HttpController):
    Route = "/items/{id}/buy"
    Endpoints = [
        Endpoint(method="get"),
    ]
    Permissions = {
        "post": "slimebones.orwynn-rbac.testing.buy-item-permission:do",
    }

    def post(self, id: str) -> dict:
        return {"item": id}


@pytest.fixture
def get_item_permission_id(
    permission_service: PermissionService,
) -> str:
    return permission_service.get(PermissionSearch(
        names=["slimebones.orwynn-rbac.testing.item-permission:get"],
    ))[0].getid()


@pytest.fixture
def update_item_permission_id(
    permission_service: PermissionService,
) -> str:
    return permission_service.get(PermissionSearch(
        names=["slimebones.orwynn-rbac.testing.item-permission:update"],
    ))[0].getid()


@pytest.fixture
def do_buy_item_permission_id(
    permission_service: PermissionService,
) -> str:
    return permission_service.get(PermissionSearch(
        names=["slimebones.orwynn-rbac.testing.buy-item-permission:do"],
    ))[0].getid()


@pytest.fixture(autouse=True)
def run_around_tests():
    os.environ["ORWYNN_MODE"] = "test"

    yield

    # Ensure that workers created in previous test does not migrate in the
    # next one
    _discard_workers()


def _discard_workers(W: type[Worker] = Worker):
    for NestedW in W.__subclasses__():
        _discard_workers(NestedW)
    W.discard(should_validate=False)
    os.environ["ORWYNN_MODE"] = ""
    os.environ["ORWYNN_ROOT_DIR"] = ""
    os.environ["ORWYNN_APPRC_PATH"] = ""


@pytest_asyncio.fixture
async def main_boot() -> AsyncGenerator:
    boot: Boot = await Boot.create(
        Module(
            "/",
            Controllers=[
                ItemsController,
                ItemsIDController,
                ItemsIDBuyController,
            ],
            imports=[rbac_module, mongo_module],
        ),
        bootscripts=[
            RBACBoot(
                default_roles=DefaultRoles,
            ).get_bootscript(),
        ],
        global_middleware={
            AccessMiddleware: ["*"],
        },
        apprc={
            "prod": {
                "Mongo": {
                    "url": "mongodb://localhost:9006",
                    "database_name": "orwynn-rbac-test",
                },
                "SQL": {
                    "database_kind": "sqlite",
                    "database_path": ":memory:?cache=shared",
                    "poolclass": "StaticPool",
                    "pool_size": None,
                },

            },
       },
    )

    yield boot

    mongo: Mongo = Di.ie().find("Mongo")
    mongo.drop_database()


@pytest.fixture
def permission_service(main_boot) -> PermissionService:
    return validation.apply(
        Di.ie().find("PermissionService"),
        PermissionService,
    )


@pytest.fixture
def role_service(main_boot) -> RoleService:
    return validation.apply(
        Di.ie().find("RoleService"),
        RoleService,
    )


@pytest.fixture
def permission_id_1(
    permission_service: PermissionService,
) -> str:
    return permission_service.get(PermissionSearch(
        names=["slimebones.orwynn-rbac.testing.item-permission:get"],
    ))[0].getid()


@pytest.fixture
def permission_id_2(
    permission_service: PermissionService,
) -> str:
    return permission_service.get(PermissionSearch(
        names=["slimebones.orwynn-rbac.testing.buy-item-permission:do"],
    ))[0].getid()


@pytest.fixture
def permission_id_3(
    permission_service: PermissionService,
) -> str:
    return permission_service.get(PermissionSearch(
        names=["slimebones.orwynn-rbac.testing.item-permission:update"],
    ))[0].getid()


@pytest.fixture
def role_id_1(
    role_service: RoleService,
    permission_id_1,
    permission_id_2,
) -> str:
    return role_service.create([RoleCreate(
        name="client",
        permission_ids=[
            # seller can get items and update them
            permission_id_1,
            permission_id_2,
        ],
        title="Client",
        description="They want to buy something!",
    )])[0].getid()


@pytest.fixture
def role_id_2(
    role_service: RoleService,
    permission_id_1,
    permission_id_3,
) -> str:
    return role_service.create([RoleCreate(
        name="seller",
        permission_ids=[
            permission_id_1,
            permission_id_3,
        ],
        title="Seller",
        description="They want to sell something!",
    )])[0].getid()


@pytest.fixture
def user_id_1(role_service: RoleService) -> str:
    user_id: str = "jeffbezos"
    role_service.set_for_user(user_id, RoleSearch(names=["ceo"]))
    return user_id


@pytest.fixture
def user_id_2(role_service: RoleService) -> str:
    user_id: str = "joebishop"
    role_service.set_for_user(user_id, RoleSearch(names=["guard"]))
    return user_id


@pytest.fixture
def user_id_3(role_service: RoleService, role_id_1) -> str:
    user_id: str = "apunahasapeemapetilon"
    role_service.set_for_user(user_id, RoleSearch(names=["seller"]))
    return user_id


@pytest.fixture
def user_id_4(role_service: RoleService, role_id_2) -> str:
    user_id: str = "proroksunboy"
    role_service.set_for_user(user_id, RoleSearch(names=["client"]))
    return user_id


@pytest.fixture
def app(main_boot: Boot) -> App:
    return main_boot.app


@pytest.fixture
def client(app: App) -> Client:
    return app.client


@pytest.fixture
def user_client_1(
    client: Client,
    user_id_1: str,
) -> Client:
    return client.bind_headers(
        headers={
            "user-id": user_id_1,
        },
    )


@pytest.fixture
def user_client_2(
    client: Client,
    user_id_2: str,
) -> Client:
    return client.bind_headers(
        headers={
            "user-id": user_id_2,
        },
    )


@pytest.fixture
def user_client_3(
    client: Client,
    user_id_3: str,
) -> Client:
    return client.bind_headers(
        headers={
            "user-id": user_id_3,
        },
    )

@pytest.fixture
def user_client_4(
    client: Client,
    user_id_4: str,
) -> Client:
    return client.bind_headers(
        headers={
            "user-id": user_id_4,
        },
    )

