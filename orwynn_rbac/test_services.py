
from orwynn.app.app import RequestMethod

from orwynn_rbac.models import Action
from orwynn_rbac.search import PermissionSearch
from orwynn_rbac.services import PermissionService


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
    assert {p.getid() for p in permission_service.get(PermissionSearch(
        actions=[
            Action(route="/items", method=RequestMethod.GET.value),
            Action(route="/items/{id}", method=RequestMethod.PATCH.value)
        ],
    ))} == {permission_id_1, permission_id_3}
