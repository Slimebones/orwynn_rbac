from orwynn_rbac.dtos import RoleCDTO, RoleUDTO


def test_get_roles(
    user_client,
    role_id_1,
    role_id_2,
):
    """
    Should get all roles.
    """
    data: dict = user_client.get_jsonify(
        "/roles",
        200,
    )

    roles_dto: RoleCDTO = RoleCDTO.recover(data)

    target_roles: set = {role_id_1, role_id_2}
    assert \
        {item.id for item in roles_dto.units}.intersection(target_roles) \
        == target_roles


def test_get_roles_by_name(
    user_client,
    role_id_1,
):
    """
    Should get role by name.
    """
    data: dict = user_client.get_jsonify(
        "/roles?names=client",
        200,
    )

    roles_dto: RoleCDTO = RoleCDTO.recover(data)

    assert [item.id for item in roles_dto.units] == [role_id_1]


def test_get_roles_by_names(
    user_client,
    role_id_1,
    role_id_2,
):
    """
    Should get role by several names.
    """
    data: dict = user_client.get_jsonify(
        "/roles?names=client&names=seller",
        200,
    )

    roles_dto: RoleCDTO = RoleCDTO.recover(data)

    assert \
        {item.id for item in roles_dto.units} \
            == {role_id_1, role_id_2}


def test_get_roles_id(
    user_client,
    role_id_1,
    permission_id_1,
    permission_id_2,
):
    data: dict = user_client.get_jsonify(
        f"/roles/{role_id_1}",
        200,
    )

    dto: RoleUDTO = RoleUDTO.recover(data)

    assert dto.name == "client"
    assert dto.title == "Client"
    assert dto.description == "They want to buy something!"
    assert set(dto.permission_ids) == {permission_id_1, permission_id_2}
