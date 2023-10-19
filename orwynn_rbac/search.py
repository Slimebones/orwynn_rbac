from orwynn.mongo import DocumentSearch

from orwynn_rbac.models import Action


class PermissionSearch(DocumentSearch):
    names: list[str] | None = None
    role_ids: list[str] | None = None
    actions: list[Action] | None = None
    is_dynamic: bool | None = None
