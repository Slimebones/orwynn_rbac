from orwynn.mongo import DocumentSearch

from orwynn_rbac.models import HTTPAction


class PermissionSearch(DocumentSearch):
    names: list[str] | None = None
    actions: list[HTTPAction] | None = None
    is_dynamic: bool | None = None


class RoleSearch(DocumentSearch):
    names: list[str] | None = None
    permission_ids: list[str] | None = None
    user_ids: list[str] | None = None
    is_dynamic: bool | None = None
