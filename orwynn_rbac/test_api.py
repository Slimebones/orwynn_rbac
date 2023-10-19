from orwynn_rbac.dto import RolesDto


def test_get(
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

    roles_dto: RolesDto = RolesDto.recover(data)

    target_roles: set = {role_id_1, role_id_2}
    assert \
        {item.id for item in roles_dto.units}.intersection(target_roles) \
        == target_roles


def test_get_by_name(
    user_client,
    role_id_1,
):
    """
    Should get role by name.
    """
    data: dict = user_client.get_jsonify(
        "/roles?names=actor&names=woo",
        200,
    )

    roles_dto: RolesDto = RolesDto.recover(data)

    assert [item.id for item in roles_dto.units] == [role_id_1]


def test_get_by_names(
    user_client,
    role_id_1,
    role_id_2,
):
    """
    Should get role by several names.
    """
    data: dict = user_client.get_jsonify(
        "/roles?names=actor&names=actor_2",
        200,
    )

    roles_dto: RolesDto = RolesDto.recover(data)

    assert [item.id for item in roles_dto.units] == [role_id_1, role_id_2]
