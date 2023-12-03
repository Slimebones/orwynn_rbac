from collections.abc import Sequence

from orwynn.base import ContainerDTO, UnitDTO

from orwynn_rbac.models import HTTPAction


class RoleUDTO(UnitDTO):
    name: str
    title: str | None
    description: str | None
    permission_ids: list[str]
    user_ids: list[str]


class RoleCDTO(ContainerDTO):
    Base = RoleUDTO
    units: Sequence[RoleUDTO]


class PermissionUDTO(UnitDTO):
    name: str
    actions: list[HTTPAction]
    is_dynamic: bool


class PermissionCDTO(ContainerDTO):
    Base = PermissionUDTO
    units: Sequence[PermissionUDTO]
