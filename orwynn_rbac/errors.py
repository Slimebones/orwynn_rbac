from typing import TYPE_CHECKING

from orwynn.base import Controller

from orwynn_rbac.models import HTTPAction

if TYPE_CHECKING:
    from orwynn_rbac.documents import Permission


class NoActionsForPermissionError(Exception):
    """
    If a permission has not actions attached for this boot shd.
    """
    def __init__(
        self,
        permission: "Permission",
    ) -> None:
        message: str = f"no actions defined for the permission={permission}"
        super().__init__(message)


class ActionAlreadyDefinedPermissionError(Exception):
    """
    If some action defined twice for the same permission.
    """
    def __init__(
        self,
        action: HTTPAction,
        permission: "Permission",
    ) -> None:
        message: str = \
            f"the action={action} is already defined for a" \
            f" permission={permission}"
        super().__init__(message)


class RestrictedDynamicPrefixError(Exception):
    def __init__(
        self,
        *,
        name: str,
    ) -> None:
        message: str = \
            f"name={name} cannot be dynamic prefixed"
        super().__init__(message)


class RequiredDynamicPrefixError(Exception):
    def __init__(
        self,
        *,
        name: str,
    ) -> None:
        message: str = \
            f"name={name} should be prefixed with \"dynamic\" keyword"
        super().__init__(message)


class IncorrectNamePermissionError(Exception):
    """
    Wrong chosen name for a permission (forbidden symbols, keywords, etc.).
    """
    def __init__(
        self,
        *,
        name: str,
        explanation: str,
    ):
        message: str = \
            f"incorrect permission name={name}: {explanation}"
        super().__init__(message)


class IncorrectMethodPermissionError(Exception):
    """
    Wrong chosen method for a permission.
    """
    def __init__(
        self,
        method: str,
        ControllerClass: type[Controller],
    ):
        message: str = \
            f"cannot assign method={method} for controller" \
            f" class={ControllerClass}"
        super().__init__(message)


class DisablingDynamicPermissionError(Exception):
    """
    Cannot disable a dynamic permission.
    """
    def __init__(
        self,
        permission: "Permission",
    ):
        message: str = f"cannot disable a dynamic permission {permission}"
        super().__init__(message)


class NonDynamicPermissionError(Exception):
    """
    A permission should be dynamic in order to make action.
    """
    def __init__(
        self,
        *,
        permission_name: str,
        in_order_to: str,
    ) -> None:
        message: str = \
            f"permission with name <{permission_name}> should be dynamic in" \
            f" order to {in_order_to}"
        super().__init__(message)
