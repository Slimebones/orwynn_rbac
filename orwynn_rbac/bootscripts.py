from antievil import NotFoundError
from orwynn.bootscript import Bootscript, CallTime
from orwynn.di.di import Di

from orwynn_rbac.constants import BootStateFlagName
from orwynn_rbac.models import DefaultRole
from orwynn_rbac.services import PermissionService, RoleService


class RBACBoot:
    def __init__(
        self,
        default_roles: list[DefaultRole]
    ) -> None:
        self._default_roles = default_roles

    def get_bootscript(self) -> Bootscript:
        return Bootscript(
            fn=self._boot,
            call_time=CallTime.AFTER_ALL
        )

    def _boot(
        self,
        role_repo: RoleService,
        permission_repo: PermissionService,
    ) -> None:
        """
        Initializes all default roles and builtin permissions.

        Should be called on each application boot, since it will scan all
        initialized controllers in order to boot correct permissions. For
        unaffected databases it will initialize default roles.
        """
        # Initialize permissions in any case since they should be calculated
        # dynamically for each boot.
        permission_repo.initialize_permissions(
            controllers=Di.ie().controllers,
        )

        with SHD.new(sql) as shd:
            state_flag: StateFlag
            try:
                state_flag = SQLUtils.get_state_flag_by_name(
                    BootStateFlagName,
                    shd,
                )
            except NotFoundError:
                state_flag = StateFlag(
                    name=BootStateFlagName,
                    value=False,
                )
                shd.add(state_flag)
                shd.commit()
                shd.refresh(state_flag)

            if state_flag.value is False:
                SQLUtils.set_state_flag_by_name(BootStateFlagName, True, shd)
                shd.commit()

                # For the first initialization of this database, call roles
                # initialization
                role_repo.initialize_defaults()
