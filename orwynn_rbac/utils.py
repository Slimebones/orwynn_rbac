import re
from typing import Any, Self

from orwynn.base import Controller, Model
from orwynn.helpers.web import (
    REQUEST_METHOD_BY_PROTOCOL,
    GenericRequest,
)
from orwynn.http import HttpController
from orwynn.url import URLMethod, URLScheme
from orwynn.websocket import WebsocketController
from pykit import validation
from pykit.cls import Static
from pykit.errors import EmptyInputError, NotFoundError, UnsupportedError

from orwynn_rbac.constants import DynamicPrefix
from orwynn_rbac.enums import PermissionAbstractAction
from orwynn_rbac.errors import (
    IncorrectMethodPermissionError,
    IncorrectNamePermissionError,
)
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
        controller: Controller,
    ) -> ControllerPermissions:
        """
        Returns dictionary {method: permission} for given controller.

        Returns:
            Controller permission by method.

        Raises:
            NotFoundError:
                No permissions found for the controller.
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
                controller.Permissions,  # type: ignore
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

        if controller_permissions is {}:
            raise NotFoundError(
                title="no permissions found for a controller",
                value=controller,
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
            request_method: URLMethod = URLMethod(method.lower())
        except ValueError as err:
            raise UnsupportedError(
                title="request method",
                value=method,
            ) from err

        if (
            (
                request_method in REQUEST_METHOD_BY_PROTOCOL[URLScheme.HTTP]
                and not issubclass(ControllerClass, HttpController)
            )
            or
                (
                    request_method
                        in REQUEST_METHOD_BY_PROTOCOL[URLScheme.Websocket]
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
        - first section may consist of several words in KeyCode format and it
            is a target of the permission
        - second section consists of 1 word and it is a name of an action (see
            PermissionAbstractAction for the list of such action names)

        Examples:
        - "slimebones.orwynn-rbac.objectives-permission:create"
        - "slimebones.orwynn-rbac.cover-list-permission:get"
        - "slimebones.orwynn-rbac.user-permission:update"
        - "slimebones.orwynn-rbac.route-card-permission:delete"

        Raises:
            IncorrectNamePermissionError:
                On any described above rule failure.
        """
        raw_action: str
        name: str

        try:
            name, raw_action = fullname.split(":")
        # Not enough values to unpack
        except ValueError as err:
            raise IncorrectNamePermissionError(
                name=fullname,
                explanation="missing separating colon",
            ) from err

        try:
            PermissionAbstractAction(raw_action)
        # Not valid action string
        except ValueError as err:
            raise IncorrectNamePermissionError(
                name=fullname,
                explanation=f"unrecognized action={raw_action}",
            ) from err

        try:
            # TODO(ryzhovalex): add keycode pattern or keycode lib call here
            validation.validate_re(
                name,
                r"^[a-z0-9\-\.]+$",
            )
        except validation.ValidationError as err:
            raise IncorrectNamePermissionError(
                name=fullname,
                explanation=f"invalid target name={name}",
            ) from err


class RouteUtils(Static):
    @staticmethod
    def is_request_route_registered(
        request: GenericRequest,
    ) -> bool:
        """
        Checks whether request's target route is registered in the system.

        Args:
            request:
                Any request to the system.

        Returns:
            True if the route is registered, False otherwise.
        """
        abstract_routes: list[str] = [
            route.path for route in request.app.routes
        ]

        pattern: re.Pattern
        for abstract_route in abstract_routes:
            pattern = RouteUtils.compile_route_regex(abstract_route)
            if pattern.fullmatch(request.url.path):
                return True

        return False

    @staticmethod
    def compile_route_regex(
        abstract_route: str,
    ) -> re.Pattern:
        """
        Compiles given abstract route into regex pattern for matching real
        routes.

        Args:
            Abstract route to create pattern from.

        Returns:
            Regex pattern.
        """
        # Avoid regex symbols in origin abstract route
        abstract_route = re.escape(abstract_route)
        return re.compile(re.sub(
            # Two slashes ahead of each of the bracket symbols {} is required
            # since initial abstract route was escaped ("{" transformed into
            # "\{")
            r"\\{.*\\}",
            # don't match following route if a format bracket is encountered,
            # e.g.  "/users/some-id/route1/route2" shouldn't be matched for
            # abstract "/users/{id}"
            r"[^\/]*",
            abstract_route,
        ))

    @staticmethod
    def find_by_abstract_route(
        abs_route: str,
        controllers: list[Controller],
    ) -> tuple[int, Controller]:
        for i, c in enumerate(controllers):
            if c.Route == abs_route:
                return (i, c)

        raise NotFoundError(
            title="controller for abs route",
            value=abs_route,
        )


class BaseUpdateOperator(Model):
    set: dict[str, Any] | None = None
    inc: dict[str, Any] | None = None
    push: dict[str, Any] | None = None
    pull: dict[str, Any] | None = None


UpdateOperatorFieldSpec = dict[str, tuple[type | list[type], list[str]]]
class UpdateOperator(BaseUpdateOperator):
    """
    Mongo-like update operator.

    Used e.g. in HTTP PUT and PATCH requests for flexible data manipulation.
    """
    id: str

    @classmethod
    def from_base(
        cls,
        id: str,
        base: BaseUpdateOperator,
    ) -> Self:
        d: dict[str, Any] = {
            "id": id,
        }
        d.update(base.dict())
        return cls.parse_obj(d)

    def get_mongo_update_query(
        self,
        field_spec: UpdateOperatorFieldSpec,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}

        for operator_name, operator_value in self.dict().items():
            if operator_name == "id" or operator_value is None:
                continue

            for field_name, field_value in operator_value.items():
                validation.validate(field_name, str)

                dollar_operator_name: str = "$" + operator_name

                if (
                    field_name in field_spec
                    and dollar_operator_name in field_spec[field_name][1]
                ):
                    validation.validate(field_value, field_spec[field_name][0])
                    if dollar_operator_name not in query:
                        query[dollar_operator_name] = {}
                    query[dollar_operator_name][field_name] = field_value

        if not query:
            raise EmptyInputError(
                title=f"update operator {self}",
            )

        return query
