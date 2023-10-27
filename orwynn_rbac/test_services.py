
from orwynn.app.app import RequestMethod
from orwynn.base import Controller
from orwynn.di.di import Di

from orwynn_rbac.models import Action
from orwynn_rbac.search import PermissionSearch, RoleSearch
from orwynn_rbac.services import PermissionService, RoleService
from orwynn_rbac.testing import DefaultRoles
from orwynn_rbac.utils import RouteUtils


def test_permission_get_by_ids(
    permission_id_1: str,
    permission_id_3: str,
    permission_service: PermissionService
):
    assert {p.getid() for p in permission_service.get(PermissionSearch(
        ids=[permission_id_1, permission_id_3],
    ))} == {permission_id_1, permission_id_3}


def test_permission_get_by_names(
    permission_id_1: str,
    permission_id_3: str,
    permission_service: PermissionService
):
    assert {p.getid() for p in permission_service.get(PermissionSearch(
        names=["get:item", "update:item"]
    ))} == {permission_id_1, permission_id_3}


def test_permission_get_by_actions(
    permission_id_1: str,
    permission_id_3: str,
    permission_service: PermissionService
):
    controllers: list[Controller] = Di.ie().controllers

    assert {p.getid() for p in permission_service.get(PermissionSearch(
        actions=[
            Action(
                controller_no=RouteUtils.find_by_abstract_route(
                    "/items", controllers
                )[0],
                method=RequestMethod.GET.value
            ),
            Action(
                controller_no=RouteUtils.find_by_abstract_route(
                    "/items/{id}", controllers
                )[0],
                method=RequestMethod.PATCH.value
            ),
        ],
    ))} == {permission_id_1, permission_id_3}


def test_default_roles(
    role_service: RoleService
):
    input_default_role_names: set[str] = {r.name for r in DefaultRoles}
    output_default_role_names: set[str] = {
        r.name for r in role_service.get(RoleSearch())
    }

    assert input_default_role_names == output_default_role_names
