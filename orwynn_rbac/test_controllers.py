from orwynn_rbac.dtos import RoleCDTO, RoleUDTO
from orwynn_rbac.services import RoleService


def test_get_roles(
    user_client_1,
    role_id_1,
    role_id_2,
):
    """
    Should get all roles.
    """
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
    assert data["value"]["code"].lower() == "error.forbidden"


def test_patch_role_id(
    user_client_1,
    role_id_1,
    permission_id_1,
    permission_id_2,
    role_service: RoleService
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
                "permission_ids": permission_id_2
            }
        }
    )

    returned_dto: RoleUDTO = RoleUDTO.recover(data)
    new_dto: RoleUDTO = role_service.get_udto(role_id_1)

    assert new_dto.name == "new-name"
    assert new_dto.title == "new-title"
    assert new_dto.description == "new-description"
    assert new_dto.permission_ids == [permission_id_1]
    assert returned_dto == new_dto
