from typing import Any

from orwynn.mongo import Document
from pykit import validation
from pykit.errors import EmptyInputError

from orwynn_rbac.errors import (
    RequiredDynamicPrefixError,
    RestrictedDynamicPrefixError,
)
from orwynn_rbac.models import HTTPAction
from orwynn_rbac.utils import NamingUtils


class Permission(Document):
    """
    Allowed action to perform.

    Attributes:
        name:
            Human-friendly readable field, e.g. "write:objectives".
        actions:
            List of actions allowed by this permission.
        is_dynamic:
            Whether this permission is dynamic.
    """
    name: str
    actions: list[HTTPAction] | None = None
    is_dynamic: bool

    def __init__(self, **data: Any) -> None:
        is_dynamic: bool = validation.apply(data["is_dynamic"], bool)
        data["name"] = self._validate_name(data["name"], is_dynamic)

        super().__init__(**data)

    def __str__(self) -> str:
        return f"Permission \"{self.name}\""

    def _validate_name(self, value: Any, is_dynamic: bool) -> Any:
        self._validate_name_not_empty(value)
        self._validate_name_dynamic_prefix(value, is_dynamic)

        return value

    def _validate_name_not_empty(self, name: str) -> None:
        if not name:
            raise EmptyInputError(
                title="permission name",
            )

    def _validate_name_dynamic_prefix(
        self, name: str, is_dynamic: bool,
    ) -> None:
        _has_dynamic_prefix: bool = NamingUtils.has_dynamic_prefix(name)

        if is_dynamic and not _has_dynamic_prefix:
            raise RequiredDynamicPrefixError(
                name=name,
            )
        elif not is_dynamic and _has_dynamic_prefix:
            raise RestrictedDynamicPrefixError(
                name=name,
            )

    @classmethod
    def _get_collection(cls) -> str:
        return "permission_rbac"


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
