from typing import TYPE_CHECKING

from orwynn.bootscript import Bootscript, CallTime
from orwynn.di.di import Di
from orwynn.log import Log
from orwynn.mongo import MongoStateFlagService
from pykit.func import FuncSpec

from orwynn_rbac.constants import RoleBootStateFlagName
from orwynn_rbac.models import DefaultRole
from orwynn_rbac.services import PermissionService, RoleService

if TYPE_CHECKING:
    from orwynn_rbac.documents import Role


class RBACBoot:
    def __init__(
        self,
        *,
        default_roles: list[DefaultRole] | None = None,
        unauthorized_user_permissions: list[str] | None = None,
        authorized_user_permissions: list[str] | None = None,
    ) -> None:
        self._default_roles: list[DefaultRole] | None = default_roles
        self._unauthorized_user_permissions: list[str] | None = \
            unauthorized_user_permissions
        self._authorized_user_permissions: list[str] | None = \
            authorized_user_permissions

    def get_bootscript(self) -> Bootscript:
        return Bootscript(
            fn=self._boot,
            call_time=CallTime.AFTER_ALL,
        )

    def _boot(
        self,
        role_service: RoleService,
        permission_service: PermissionService,
        mongo_state_flag_service: MongoStateFlagService,
    ) -> None:
        """
        Initializes all default roles and builtin permissions.

        Should be called on each application boot, since it will scan all
        initialized controllers in order to boot correct permissions. For
        unaffected databases it will initialize default roles.
        """
        # Initialize permissions in any case since they should be calculated
        # dynamically for each boot.
        deleted_permission_ids: set[str]
        _, deleted_permission_ids = \
            permission_service._init_internal(  # noqa: SLF001
                controllers=Di.ie().controllers,
            )

        if self._default_roles:
            initialized_roles: list[Role] | None = \
                mongo_state_flag_service.decide(
                    key=RoleBootStateFlagName,
                    on_false=FuncSpec(
                        fn=role_service._init_defaults_internal, # noqa: SLF001
                        args=(
                            self._default_roles,
                            self._unauthorized_user_permissions,
                            self._authorized_user_permissions,
                        ),
                    ),
                    finally_set_to=True,
                    default_flag_on_not_found=False,
                )

            if initialized_roles:
                role_names: str = ", ".join(
                    [r.name for r in initialized_roles],
                )
                Log.info(
                    f"[orwynn_rbac] default roles initialized: {role_names}",
                )

        if deleted_permission_ids:
            Log.info(
                "[orwynn_rbac] schedule permissions for delete: "
                + ", ".join(deleted_permission_ids),
            )
            role_service._unlink_internal(list(  # noqa: SLF001
                deleted_permission_ids,
            ))
