from typing import Literal

"""
List of permission names for creating dynamic permissions.

Each of these names is handled according to special logic - according to these
names lists of actions allowed for a dynamic permissions are created.

Names:
    uncovered:
        Adds to actions all controller's method for which the
        controller.PERMISSION attribute is not set.
"""
DynamicName = Literal[
    "uncovered"
]
