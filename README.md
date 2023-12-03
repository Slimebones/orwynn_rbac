# 👮 Role-Based-Access-Control module for Orwynn framework

Gives controls to roles and their permissions in your backend application.


## Installation

Via Poetry:
```sh
poetry add orwynn_rbac
```

## Usage

Define default roles in your application:
```python
DefaultRoles = [
    DefaultRole(
        name="sergeant",
        title="Sergeant",
        description="Flexible policeman",
        permission_names=set(
            "yourcompany.yourproject.citizen.citizen-permission:get",
            "yourcompany.yourproject.tax.tax-permission:create",
            "yourcompany.yourproject.pursue.start-permission:do"
        )
    ),
    ...
]
```

> NOTE: Default roles are initialized only once per fresh database.

In your Boot setup, initialize a RBACBoot class and get a bootscript from it:
```python
from orwynn_rbac import RBACBoot

Boot(
    ...,
    bootscripts=[
        ...,
        RBACBoot(
            default_roles=DefaultRoles
        ).get_bootscript()
    ]
)
```

In any module, where RBAC functionality is required (e.g. user access
checkers), import `orwynn_rbac.module`:
```python
import orwynn_rbac

your_module = Module(
    ...,
    imports=[
        ...,
        orwynn_rbac.module
    ]
)
```

### Checking access

To check an access to your controller you are free to implement own middleware,
retrieve an user id, e.g. from HTTP authorization header, and pass it to our
`AccessService.check_user()` method. A minimal middleware might look like this:

```python
class AccessMiddleware(HttpMiddleware):
    def __init__(
        self,
        covered_routes: list[str],
        service: AccessService,
    ) -> None:
        super().__init__(covered_routes)
        self.service: AccessService = service

    async def process(
        self,
        request: HttpRequest,
        call_next: Callable,
    ) -> HttpResponse:
        user_id: str | None = request.headers.get("user-id", None)
        self.service.check_user(
            user_id, str(request.url.components.path), request.method
        )

        response: HttpResponse = await call_next(request)

        return response
```

The method `AccessService.check_user()` will raise a `ForbiddenError` if an
user with given id has no access to the route and method, so you just need to
call it with these arguments.
