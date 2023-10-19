from collections.abc import Sequence

from orwynn.utils.dto import ContainerDTO, UnitDTO


class RoleDto(UnitDTO):
    name: str
    title: str | None
    description: str | None
    permission_ids: list[str]
    user_ids: list[str]


class RolesDto(ContainerDTO):
    Base = RoleDto
    units: Sequence[RoleDto]
