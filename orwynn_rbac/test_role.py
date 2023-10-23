from orwynn.utils import validation

from orwynn_rbac.documents import Role
from orwynn_rbac.errors import (
    RequiredDynamicPrefixError,
    RestrictedDynamicPrefixError,
)


def test_create_generic_with_dynamic_prefix():
    """
    Should raise an error on generic role creation with "dynamic:" prefixed
    name.
    """
    validation.expect(
        Role,
        RestrictedDynamicPrefixError,
        name="dynamic:ihaterules",
        _is_dynamic=False,
    )
    # Also for implicit argument
    validation.expect(
        Role,
        RestrictedDynamicPrefixError,
        name="dynamic:ihaterules",
    )


def test_create_dynamic_without_dynamic_prefix():
    """
    Should raise an error on dynamic role creation without "dynamic:" prefixed
    name.
    """
    validation.expect(
        Role,
        RequiredDynamicPrefixError,
        name="helloworld",
        _is_dynamic=True,
    )
