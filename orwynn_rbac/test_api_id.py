from orwynn_rbac.dto import RoleDto


def test_get(
    user_client,
    role_id_1,
    permission_id_1,
    permission_id_2,
):
    data: dict = user_client.get_jsonify(
        f"/roles/{role_id_1}",
        200,
    )

    dto: RoleDto = RoleDto.recover(data)

    assert dto.name == "actor"
    assert dto.title == "Some actor"
    assert dto.description == "Some actor description"
    assert set(dto.permission_ids) == {permission_id_1, permission_id_2}
