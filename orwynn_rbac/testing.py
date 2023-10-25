from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from orwynn.base import Module
from orwynn.boot import Boot
from orwynn.di.di import Di
from orwynn.http import Endpoint, HttpController
from orwynn.utils import validation

from orwynn_rbac import module as rbac_module
from orwynn_rbac.bootscripts import RBACBoot
from orwynn_rbac.models import RoleCreate
from orwynn_rbac.search import PermissionSearch
from orwynn_rbac.services import PermissionService, RoleService

if TYPE_CHECKING:
    pass


class ItemsController(HttpController):
    ROUTE = "/items"
    ENDPOINTS = [
        Endpoint(method="get"),
    ]
    Permissions = {
        "get": "get:item"
    }

    def get(self) -> dict:
        return {"item": "all"}


class ItemsIDController(HttpController):
    ROUTE = "/items/{id}"
    ENDPOINTS = [
        Endpoint(method="get"),
    ]
    Permissions = {
        "patch": "update:item"
    }

    def patch(self, id: str) -> dict:
        return {"item": id}


class ItemsIDBuyController(HttpController):
    ROUTE = "/items/{id}/buy"
    ENDPOINTS = [
        Endpoint(method="get"),
    ]
    Permissions = {
        "post": "do:buy-item"
    }

    def post(self, id: str) -> dict:
        return {"item": id}


@pytest_asyncio.fixture
async def main_boot() -> Boot:
    return await Boot.create(
        Module("/", imports=[rbac_module]),
        bootscripts=[
            RBACBoot().get_bootscript()
        ],
        apprc={
            "prod": {
                "Mongo": {
                    "url": "mongodb://localhost:9006",
                    "database_name": "orwynn-rbac-test"
                },
                "SQL": {
                    "database_kind": "sqlite",
                    "database_path": ":memory:?cache=shared",
                    "poolclass": "StaticPool",
                    "pool_size": None
                }

            }
       }
    )


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
        names=["get:item"],
    ))[0].getid()


@pytest.fixture
def permission_id_2(
    permission_service: PermissionService,
) -> str:
    return permission_service.get(PermissionSearch(
        names=["do:buy-item"],
    ))[0].getid()


@pytest.fixture
def permission_id_3(
    permission_service: PermissionService,
) -> str:
    return permission_service.get(PermissionSearch(
        names=["update:item"],
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
            permission_id_2
        ],
        title="Client",
        description="They want to buy something!"
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
            permission_id_3
        ],
        title="Seller",
        description="They want to sell something!"
    )])[0].getid()
