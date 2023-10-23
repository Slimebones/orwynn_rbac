from orwynn.mongo import DocumentSearch

from orwynn_rbac.models import Action


class PermissionSearch(DocumentSearch):
    names: list[str] | None = None
    actions: list[Action] | None = None
    is_dynamic: bool | None = None


class RoleSearch(DocumentSearch):
    names: list[str] | None = None
    permissions_ids: list[str] | None = None
    user_ids: list[str] | None = None
    is_dynamic: bool | None = None
