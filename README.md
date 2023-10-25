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
            "get:lowlifes",
            "post:issue-tax",
            "post:start-pursue"
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
