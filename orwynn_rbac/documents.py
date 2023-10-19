from typing import Any
from antievil import EmptyInputError
from orwynn.mongo import Document

from sqlalchemy.orm import Mapped, mapped_column

from orwynn_rbac.errors import (
    RequiredDynamicPrefixError,
    RestrictedDynamicPrefixError,
)
from orwynn_rbac.models import Action
from orwynn_rbac.utils import NamingUtils


class Permission(Document):
    """
    Allowed action to perform.

    Attributes:
        name:
            Human-friendly readable field, e.g. "write:objectives".
        actions:
            List of actions allowed by this permission.
        role_ids:
            Ids of roles connected to this permission.
        is_dynamic:
            Whether this permission is dynamic.
    """
    name: str

    role_ids: list[str] = []
    actions: list["Action"] = []

    # See DynamicPermissionModel
    is_dynamic: Mapped[bool] = mapped_column(default=False)

    def __init__(self, **data: Any) -> None:
        data["name"] = self._validate_name(data["name"])

        super().__init__(**data)

    def __str__(self) -> str:
        return f"Permission \"{self.name}\""

    def _validate_name(self, value: Any) -> Any:
        self._validate_name_not_empty(value)
        self._validate_name_dynamic_prefix(value)

        return value

    def _validate_name_not_empty(self, name: str) -> None:
        if not name:
            raise EmptyInputError(
                title="permission name",
            )

    def _validate_name_dynamic_prefix(self, name: str) -> None:
        _has_dynamic_prefix: bool = NamingUtils.has_dynamic_prefix(name)

        if self.is_dynamic and not _has_dynamic_prefix:
            raise RequiredDynamicPrefixError(
                name=name,
            )
        elif self.is_dynamic and _has_dynamic_prefix:
            raise RestrictedDynamicPrefixError(
                name=name,
            )


class Role(Document):
    name: str

    title: str | None = None
    description: str | None = None

    permission_ids: list[str] = []
    user_ids: list[str] = []

    # A role with dynamic users affected.
    #
    # Such roles cannot be deleted, nor changed and are based on implementation
    # detail. But the set of permission for such roles are editable by the
    # external client.
    #
    # The dynamic role has nothing written in "user_ids" field, all affected
    # users are calculated at the request-time.
    #
    # For example "not-authorized" is the typical dynamic role with all
    # non-authorized users affected.
    #
    # All these roles should be prefixed by keyword "dynamic:" to avoid
    # conflicts with general role names. If a name is not prefixed with such
    # keyword on a new row's creation or during property setting, a
    # DynamicPrefixError is raised.
    is_dynamic: bool

    def __str__(self) -> str:
        return f"<role {self.name}>"

    @classmethod
    def _get_collection(cls) -> str:
        return "role_rbac"
