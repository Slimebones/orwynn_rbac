from orwynn.base.model import Model


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
    title: str | None = None
    description: str | None = None

    permission_ids: list[str] | None = None


class RoleCreateMany(Model):
    arr: list[RoleCreate]


class HTTPAction(Model):
    """
    Represents a target route and used method of an action.
    """
    controller_no: int
    method: str

    @property
    def mongovalue(self) -> dict:
        return self.dict()
