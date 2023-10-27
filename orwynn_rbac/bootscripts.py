from orwynn.bootscript import Bootscript, CallTime
from orwynn.di.di import Di
from orwynn.log import Log
from orwynn.utils.func import FuncSpec

from orwynn_rbac.constants import RoleBootStateFlagName
from orwynn_rbac.documents import Permission, Role
from orwynn_rbac.models import DefaultRole
from orwynn_rbac.mongo_state_flag import MongoStateFlagService
from orwynn_rbac.services import PermissionService, RoleService


class RBACBoot:
    def __init__(
        self,
        *,
        default_roles: list[DefaultRole] | None = None
    ) -> None:
        self._default_roles: list[DefaultRole] | None = default_roles

    def get_bootscript(self) -> Bootscript:
        return Bootscript(
            fn=self._boot,
            call_time=CallTime.AFTER_ALL
        )

    def _boot(
        self,
        role_service: RoleService,
        permission_service: PermissionService,
        mongo_state_flag_service: MongoStateFlagService
    ) -> None:
        """
        Initializes all default roles and builtin permissions.

        Should be called on each application boot, since it will scan all
        initialized controllers in order to boot correct permissions. For
        unaffected databases it will initialize default roles.
        """
        # Initialize permissions in any case since they should be calculated
        # dynamically for each boot.
        permission_service._init_internal(
            controllers=Di.ie().controllers,
        )

        if not self._default_roles:
            return

        initialized_roles: list[Role] | None = mongo_state_flag_service.decide(
            key=RoleBootStateFlagName,
            on_false=FuncSpec(
                fn=role_service._init_defaults_internal,
                args=(self._default_roles,)
            ),
            finally_set_to=True,
            default_flag_on_not_found=False
        )

        if initialized_roles:
            role_names: str = ", ".join([r.name for r in initialized_roles])
            Log.info(
                f"[orwynn_rbac] default roles initialized: {role_names}"
            )
