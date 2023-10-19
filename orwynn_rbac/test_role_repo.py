from typing import TYPE_CHECKING

import pytest
from orwynn.base import Module
from orwynn.boot import Boot
from orwynn.di.di import Di
from orwynn.http import Endpoint, HttpController
from orwynn.sql import Sql
from orwynn.sql import module as sql_module
from orwynn.utils import validation
from pycore.errors import NotFoundError
from pycore.usql import Shd

from src import rbac
from orwynn_rbac.default import DefaultRole

if TYPE_CHECKING:
    from orwynn_rbac.services import PermissionService
    from orwynn_rbac.services import RoleRepo
    from orwynn_rbac.documents import Role


class _ExampleController(HttpController):
    ROUTE = "/"
    ENDPOINTS = [
        Endpoint(
            method="get",
        ),
        Endpoint(
            method="post",
        ),
    ]
    PERMISSIONS = {
        "get": "get:example",
        "post": "create:example",
    }


@pytest.mark.asyncio
async def test_initialize_defaults():
    """
    Should correctly initialize default roles.
    """
    await Boot.create(
        root_module=Module(
            route="/",
            Controllers=[_ExampleController],
            imports=[
                sql_module,
                rbac.module,
            ],
        ),
    )
    sql: Sql = Di.ie().find("Sql")
    sql.create_tables()

    permission_repo: PermissionService = Di.ie().find("PermissionRepo")
    permission_repo.initialize_permissions(
        controllers=[Di.ie().find("_ExampleController")],
    )

    role_repo: RoleRepo = Di.ie().find("RoleRepo")
    role_repo.initialize_defaults([
        DefaultRole(
            name="novice",
            permission_names={
                "get:example",
            },
        ),
        DefaultRole(
            name="niceguy",
            permission_names={
                "get:example",
                "create:example",
            },
        ),
    ])

    with Shd.new(sql) as shd:
        roles: list[Role] = role_repo.get_all(shd)

        for role in roles:
            match role.name:
                case "novice":
                    assert len(role.permissions) == 1
                    assert role.permissions[0].name == "get:example"
                    assert not role.permissions[0].is_dynamic
                case "niceguy":
                    assert {p.name for p in role.permissions} == {
                        "get:example",
                        "create:example",
                    }
                    assert not any(p.is_dynamic for p in role.permissions)
                case _:
                    raise AssertionError


@pytest.mark.asyncio
async def test_initialize_defaults_existing():
    """
    Should correctly initialize default roles and update existing ones.

    The application is booted first time and correctly initialized both
    initial permissions (at the moment of the first boot) and the default
    roles.

    The second boot, the set of permissions of the same controller is changed,
    so the old existing roles should adjust their relationship data.
    """
    await Boot.create(
        root_module=Module(
            route="/",
            Controllers=[_ExampleController],
            imports=[
                sql_module,
                rbac.module,
            ],
        ),
    )
    sql: Sql = Di.ie().find("Sql")
    sql.create_tables()

    # First boot #

    permission_repo: PermissionService = Di.ie().find("PermissionRepo")
    example_controller: _ExampleController = Di.ie().find("_ExampleController")
    permission_repo.initialize_permissions(
        controllers=[example_controller],
    )

    role_repo: RoleRepo = Di.ie().find("RoleRepo")
    role_repo.initialize_defaults([
        DefaultRole(
            name="novice",
            permission_names={
                "get:example",
            },
        ),
        DefaultRole(
            name="niceguy",
            permission_names={
                "get:example",
                "create:example",
            },
        ),
    ])

    ##

    # Second boot #

    # note that the default roles are initialized only the first boot of the
    # application per database

    example_controller.PERMISSIONS = {
        "get": "get:example",
        # simulated change of permission for the second boot
        "post": "create:superexample",
    }

    # remove RAM models from the first boot
    permission_repo.clean_permission_models()
    permission_repo.initialize_permissions(
        controllers=[example_controller],
    )

    ##

    with Shd.new(sql) as shd:
        roles: list[Role] = role_repo.get_all(shd)

        for role in roles:
            match role.name:
                case "novice":
                    # novice role's permissions shouldn't change
                    assert len(role.permissions) == 1
                    assert role.permissions[0].name == "get:example"
                    assert not role.permissions[0].is_dynamic
                case "niceguy":
                    # the old permission `create:example` should be discarded
                    # for good
                    validation.expect(
                        permission_repo.get_one_by_name,
                        NotFoundError,
                        "create:example",
                        shd,
                    )
                    # and role's reference to this permission should be deleted
                    assert {p.name for p in role.permissions} == {
                        "get:example",
                    }
                    assert not any(p.is_dynamic for p in role.permissions)
                case _:
                    raise AssertionError

            # additionally, the newly created permission shouldn't
            # contain any references to roles
            assert len(permission_repo.get_one_by_name(
                "create:superexample",
                shd,
            ).roles) == 0
