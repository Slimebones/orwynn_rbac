from pykit import validation
from pykit.errors import NotFoundError

from orwynn_rbac.dtos import PermissionCDTO, RoleCDTO, RoleUDTO
from orwynn_rbac.search import RoleSearch
from orwynn_rbac.services import RoleService


def test_get_permissions(
    user_client_1,
    permission_id_1,
    permission_id_2,
):
    data: dict = user_client_1.get_jsonify(
        "/rbac/permissions",
        200,
    )

    cdto = PermissionCDTO.recover(data)

    targets: set = {permission_id_1, permission_id_2}
    assert \
        {item.id for item in cdto.units}.intersection(targets) \
        == targets


def test_get_permissions_by_ids(
    user_client_1,
    permission_id_1,
    permission_id_2,
):
    """
    Should get role by name.
    """
    data: dict = user_client_1.get_jsonify(
        "/rbac/permissions?ids=" + permission_id_1 + "&ids=" + permission_id_2,
        200,
    )

    cdto: PermissionCDTO = PermissionCDTO.recover(data)

    assert \
        [item.id for item in cdto.units] \
            == [permission_id_1, permission_id_2]


def test_get_permissions_by_names(
    user_client_1,
    permission_id_1,
    permission_id_2,
):
    """
    Should get role by several names.
    """
    data: dict = user_client_1.get_jsonify(
        "/rbac/permissions"
            + "?names=slimebones.orwynn-rbac.testing.item-permission:get"
            + "&names=slimebones.orwynn-rbac.testing.buy-item-permission:do",
        200,
    )

    cdto = PermissionCDTO.recover(data)

    assert \
        {item.id for item in cdto.units} \
            == {permission_id_1, permission_id_2}


def test_get_roles(
    user_client_1,
    role_id_1,
    role_id_2,
):
    data: dict = user_client_1.get_jsonify(
        "/rbac/roles",
        200,
    )

    roles_dto: RoleCDTO = RoleCDTO.recover(data)

    target_roles: set = {role_id_1, role_id_2}
    assert \
        {item.id for item in roles_dto.units}.intersection(target_roles) \
        == target_roles


def test_get_roles_by_name(
    user_client_1,
    role_id_1,
):
    """
    Should get role by name.
    """
    data: dict = user_client_1.get_jsonify(
        "/rbac/roles?names=seller&names=client",
        200,
    )

    roles_dto: RoleCDTO = RoleCDTO.recover(data)

    assert [item.id for item in roles_dto.units] == [role_id_1]


def test_get_roles_by_ids(
    user_client_1,
    role_id_1,
    role_id_2,
):
    """
    Should get role by name.
    """
    data: dict = user_client_1.get_jsonify(
        "/rbac/roles?ids=" + role_id_1 + "&ids=" + role_id_2,
        200,
    )

    roles_dto: RoleCDTO = RoleCDTO.recover(data)

    assert [item.id for item in roles_dto.units] == [role_id_1, role_id_2]


def test_get_roles_by_names(
    user_client_1,
    role_id_1,
    role_id_2,
):
    """
    Should get role by several names.
    """
    data: dict = user_client_1.get_jsonify(
        "/rbac/roles?names=client&names=seller",
        200,
    )

    roles_dto: RoleCDTO = RoleCDTO.recover(data)

    assert \
        {item.id for item in roles_dto.units} \
            == {role_id_1, role_id_2}


def test_get_roles_id(
    user_client_1,
    role_id_1,
    permission_id_1,
    permission_id_2,
):
    data: dict = user_client_1.get_jsonify(
        f"/rbac/roles/{role_id_1}",
        200,
    )

    dto: RoleUDTO = RoleUDTO.recover(data)

    assert dto.name == "client"
    assert dto.title == "Client"
    assert dto.description == "They want to buy something!"
    assert set(dto.permission_ids) == {permission_id_1, permission_id_2}


def test_get_roles_forbidden(
    user_client_2,
    role_id_1,
    permission_id_1,
    permission_id_2,
):
    data: dict = user_client_2.get_jsonify(
        "/rbac/roles",
        400,
    )

    assert data["type"] == "error"
    assert data["value"]["code"].lower() == \
        "slimebones.pykit.errors.forbidden-error"


def test_patch_role_id(
    user_client_1,
    role_id_1,
    permission_id_1,
    permission_id_2,
    role_service: RoleService,
):
    data: dict = user_client_1.patch_jsonify(
        f"/rbac/roles/{role_id_1}",
        200,
        json={
            "set": {
                "name": "new-name",
                "title": "new-title",
                "description": "new-description",
            },
            "pull": {
                "permission_ids": permission_id_2,
            },
        },
    )

    returned_dto: RoleUDTO = RoleUDTO.recover(data)
    new_dto: RoleUDTO = role_service.get_udto(role_id_1)

    assert new_dto.name == "new-name"
    assert new_dto.title == "new-title"
    assert new_dto.description == "new-description"
    assert new_dto.permission_ids == [permission_id_1]
    assert returned_dto == new_dto


def test_patch_role_id_forbidden(
    user_client_2,
    role_id_1,
    permission_id_2,
):
    data: dict = user_client_2.patch_jsonify(
        f"/rbac/roles/{role_id_1}",
        400,
        json={
            "set": {
                "name": "new-name",
                "title": "new-title",
                "description": "new-description",
            },
            "pull": {
                "permission_ids": permission_id_2,
            },
        },
    )

    assert data["type"] == "error"
    assert data["value"]["code"].lower() == \
        "slimebones.pykit.errors.forbidden-error"


def test_post_roles(
    role_service,
    user_client_1,
    get_item_permission_id,
    update_item_permission_id,
    do_buy_item_permission_id,
):
    data: dict = user_client_1.post_jsonify(
        "/rbac/roles",
        200,
        json={
            "arr": [
                {
                    "name": "new-role_1",
                    "title": "New Role 1",
                    "permission_ids": [
                        get_item_permission_id,
                        update_item_permission_id,
                    ],
                },
                {
                    "name": "new-role_2",
                    "title": "New Role 2",
                    "permission_ids": [
                        update_item_permission_id,
                        do_buy_item_permission_id,
                    ],
                },
            ],
        },
    )

    cdto: RoleCDTO = RoleCDTO.recover(data)

    assert cdto.units[0].name == "new-role_1"
    assert cdto.units[0].title == "New Role 1"
    assert cdto.units[0].permission_ids == [
        get_item_permission_id,
        update_item_permission_id,
    ]

    assert cdto.units[1].name == "new-role_2"
    assert cdto.units[1].title == "New Role 2"
    assert cdto.units[1].permission_ids == [
        update_item_permission_id,
        do_buy_item_permission_id,
    ]

    assert {u.name for u in cdto.units} == {
        u.name for u in role_service.get_cdto(
            RoleSearch(names=["new-role_1", "new-role_2"]),
        ).units
    }


def test_delete_roles(
    user_client_1,
    role_id_1,
    role_id_2,
    role_service,
):
    data: dict = user_client_1.delete_jsonify(
        "/rbac/roles?names=client&names=seller",
        200,
    )

    cdto = RoleCDTO.recover(data)

    assert cdto.units[0].name == "client"
    assert cdto.units[1].name == "seller"
    validation.expect(
        role_service.get,
        NotFoundError,
        RoleSearch(
            names=["client", "seller"],
        ),
    )


def test_delete_role(
    user_client_1,
    role_id_1,
    role_service,
):
    data: dict = user_client_1.delete_jsonify(
        f"/rbac/roles/{role_id_1}",
        200,
    )

    udto = RoleUDTO.recover(data)

    assert udto.name == "client"
    validation.expect(
        role_service.get,
        NotFoundError,
        RoleSearch(
            names=["client"],
        ),
    )
