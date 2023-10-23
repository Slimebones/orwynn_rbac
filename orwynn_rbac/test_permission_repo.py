import pytest
from orwynn import sql
from orwynn.base import Module
from orwynn.boot import Boot
from orwynn.bootscript import Bootscript
from orwynn.di.di import Di
from src.helpers.bootscripts import BOOTSCRIPTS

from orwynn_rbac.permission.testing import (
    ReadPermissionController,
)
from orwynn_rbac.services import PermissionService


@pytest.fixture
def _initialize_permissions(
    permission_repo: PermissionService,
    di: Di,
) -> None:
    permission_repo.initialize_permissions(
        controllers=di.controllers,
    )


@pytest.fixture
def _bootscripts() -> list[Bootscript]:
    return [
        BOOTSCRIPTS["create_tables"],
        BOOTSCRIPTS["initialize_rbac"],
    ]

@pytest.mark.asyncio
async def test_initialize_permissions(
    _bootscripts: list[Bootscript],
):
    """
    Should correctly initialize permissions for a basic case.
    """
    await Boot.create(
        Module(
            "/",
            Providers=[PermissionService],
            Controllers=[ReadPermissionController],
            imports=[sql.module],
        ),
        bootscripts=[
            BOOTSCRIPTS["create_tables"],
        ],
    )

    di = Di.ie()
    # Get a new object of DI, but not from fixtures since we create an isolated
    # boot
    permission_repo: PermissionService = di.find("PermissionRepo")

    permission_repo.initialize_permissions(
        controllers=di.controllers,
    )
