from typing import TYPE_CHECKING
from orwynn.sql import SHD

import pytest
from orwynn.di.di import Di
from orwynn.utils import validation
from orwynn.http import Endpoint, HttpController

from orwynn_rbac.services import PermissionService, RoleRepo

if TYPE_CHECKING:
    from orwynn_rbac.documents import Role

GET_DATA: dict = {"message": "hello"}


class ReadPermissionController(HttpController):
    ROUTE = "/"
    ENDPOINTS = [
        Endpoint(method="get"),
    ]
    PERMISSIONS = {
        "get": "get:donuts",
    }

    def get(self) -> dict:
        return GET_DATA


@pytest.fixture
def permission_repo() -> PermissionService:
    return validation.apply(
        Di.ie().find("PermissionRepo"),
        PermissionService,
    )


@pytest.fixture
def permission_id_1(
    permission_repo: PermissionService,
) -> str:
    return permission_repo.get_model_by_name(
        "get:user",
    ).table_id


@pytest.fixture
def permission_id_2(
    permission_repo: PermissionService,
) -> str:
    return permission_repo.get_model_by_name(
        "get:role",
    ).table_id


@pytest.fixture
def role_repo() -> RoleRepo:
    return validation.apply(
        Di.ie().find("RoleRepo"),
        RoleRepo,
    )


@pytest.fixture
def role_id_1(
    role_repo: RoleRepo,
    permission_repo: PermissionService,
    permission_id_1,
    permission_id_2,
    sql,
) -> str:
    with SHD.new(sql) as shd:
        role: Role = role_repo.create(
            shd=shd,
            name="actor",
            title="Some actor",
            description="Some actor description",
            permission_names=[
                permission.name
                for permission in permission_repo.get(
                    [
                        permission_id_1,
                        permission_id_2,
                    ],
                    shd,
                )
            ],
        )

        shd.execute_final()
        shd.refresh(role)

        return role.getid()


@pytest.fixture
def role_id_2(
    role_repo: RoleRepo,
    permission_repo: PermissionService,
    permission_id_1,
    permission_id_2,
    sql,
) -> str:
    with SHD.new(sql) as shd:
        role: Role = role_repo.create(
            shd=shd,
            name="actor_2",
            title="Some actor",
            description="Some actor description",
            permission_names=[
                permission.name
                for permission in permission_repo.get(
                    [
                        permission_id_1,
                        permission_id_2,
                    ],
                    shd,
                )
            ],
        )

        shd.execute_final()
        shd.refresh(role)

        return role.getid()
