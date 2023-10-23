from orwynn.base import Model
from orwynn.base.model import Model
from orwynn.helpers.web import RequestMethod


class DefaultRole(Model):
    """
    Initialized by default on system's first deploy.
    """
    name: str
    title: str | None = None
    description: str | None = None
    permission_names: list[str]


class RoleCreate(Model):
    # if a name contains dynamic prefix, a dynamic role will be automatically
    # created
    name: str
    permission_ids: list[str]
    title: str | None = None
    description: str | None = None


class Action(Model):
    """
    Represents a target route and used method of an action.
    """
    route: str
    method: RequestMethod

    def mongovalue(self) -> dict:
        return self.dict()
