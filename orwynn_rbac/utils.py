from antievil import EmptyInputError, UnsupportedError
from orwynn.helpers.web import REQUEST_METHOD_BY_PROTOCOL, RequestMethod
from orwynn.http import HttpController
from orwynn.utils.klass import Static
from orwynn.utils.scheme import Scheme
from orwynn.websocket import WebsocketController
from orwynn.base import Controller
from orwynn.utils import validation
from orwynn_rbac.errors import IncorrectMethodPermissionError, IncorrectNamePermissionError
from orwynn_rbac.constants import DynamicPrefix
from orwynn_rbac.abstract_action import PermissionAbstractAction
from orwynn_rbac.types import ControllerPermissions


class NamingUtils(Static):
    @staticmethod
    def has_dynamic_prefix(name: str) -> bool:
        """
        Checks whether the given name has dynamic prefix.
        """
        return name.startswith(DynamicPrefix + ":")


class PermissionUtils(Static):
    @classmethod
    def collect_controller_permissions(
        cls,
        *,
        controller: Controller,
    ) -> ControllerPermissions:
        """
        Returns dictionary {method: permission} for given controller.

        Returns:
            Controller permission by method.

            If a controller does not have permission set, an empty dict is
            returned.

        Raises:
            DynamicPrefixError:
                If a controller used a permission with dynamic prefix.
            IncorrectMethodPermissionError:
                If a controller used an incorrect method for a permission.
            IncorrectNamePermissionError:
                If a controller used an incorrect name for a permission.
        """
        controller_permissions: ControllerPermissions = {}

        try:
            controller_permissions = validation.apply(
                controller.PERMISSIONS,  # type: ignore
                dict,
            )
        except AttributeError:
            pass
        else:
            validation.validate_dict(controller_permissions, (str, str))

            for method, permission_name in controller_permissions.items():
                _method: str = validation.apply(method, str)
                _permission_name: str = validation.apply(permission_name, str)

                cls._validate_method(_method, ControllerClass=type(controller))
                cls._validate_permission_name(_permission_name)

                if not _permission_name:
                    raise EmptyInputError(
                        title="permission name",
                    )

        return controller_permissions

    @classmethod
    def _validate_method(
        cls,
        method: str,
        *,
        ControllerClass: type[Controller],
    ) -> None:
        try:
            request_method: RequestMethod = RequestMethod(method.lower())
        except ValueError as err:
            raise UnsupportedError(
                title="request method",
                value=method,
            ) from err

        if (
            (
                request_method in REQUEST_METHOD_BY_PROTOCOL[Scheme.HTTP]
                and not issubclass(ControllerClass, HttpController)
            )
            or
                (
                    request_method
                        in REQUEST_METHOD_BY_PROTOCOL[Scheme.WEBSOCKET]
                    and not issubclass(ControllerClass, WebsocketController)
                )
        ):
            raise IncorrectMethodPermissionError(
                method=method,
                ControllerClass=ControllerClass,
            )

    @classmethod
    def _validate_permission_name(
        cls,
        fullname: str,
    ) -> None:
        """
        Controller permission name:
        - consist of two sections separated by colon
        - first section consists of 1 word and it is a name of an action (see
            PermissionAbstractAction for the list of such action names)
        - second section may consist of several words and it is a target of
            permission - all lower-cased alphanumeric separated by dashes on
            need

        Examples:
        - "create:objectives"
        - "get:cover-list"
        - "update:user"
        - "delete:route-card"

        Raises:
            IncorrectNamePermissionError:
                On any described above rule failure.
        """
        raw_action: str
        name: str

        try:
            raw_action, name = fullname.split(":")
        # Not enough values to unpack
        except ValueError as err:
            raise IncorrectNamePermissionError(
                name=fullname,
                explanation="missing separating colon",
            ) from err

        try:
            PermissionAbstractAction(
                raw_action,
            )
        # Not valid action string
        except ValueError as err:
            raise IncorrectNamePermissionError(
                name=fullname,
                explanation=f"unrecognized action={raw_action}",
            ) from err

        try:
            validation.validate_re(
                name,
                r"^[a-zA-Z0-9\-]+$",
            )
        except validation.ValidationError as err:
            raise IncorrectNamePermissionError(
                name=fullname,
                explanation=f"invalid target name={name}",
            ) from err
