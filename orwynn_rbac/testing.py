from typing import TYPE_CHECKING
from fastapi import Query

import pytest
from orwynn.di.di import Di
from orwynn.http import Endpoint, HttpController
from orwynn.sql import SHD
from orwynn.utils import validation
from orwynn_rbac.models import RoleCreate
from orwynn_rbac.search import PermissionSearch, RoleSearch

from orwynn_rbac.services import PermissionService, RoleService

if TYPE_CHECKING:
    from orwynn_rbac.documents import Role


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
        "get": "update:item"
    }

    def update(self, id: str) -> dict:
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


@pytest.fixture
def permission_service() -> PermissionService:
    return validation.apply(
        Di.ie().find("PermissionService"),
        PermissionService,
    )


@pytest.fixture
def role_service() -> RoleService:
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
