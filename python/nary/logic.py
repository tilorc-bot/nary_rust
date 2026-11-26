"""And, Not and Or build BoolKind expressions.

    >>> import nary as nr
    >>> from nary.logic import And, Not, Or, true
    >>> x, y = nr.NumberKind("x"), nr.NumberKind("y")
    >>> And(x < y, Not(nr.Eq(x, y)), true)
    And(Lt(x, y), Not(Eq(x, y)), true)

A Python bool is not accepted where a BoolKind is required.

    >>> Or(x < y, True)
    Traceback (most recent call last):
        ...
    TypeError: Or expects BoolKind, got bool: True
"""

from ._core import declare_constant
from .domains import declare_function
from .kinds import BoolKind, Many

__all__ = ["And", "Not", "Or", "false", "true"]

true = declare_constant("true", BoolKind)
false = declare_constant("false", BoolKind)

And = declare_function("And", Many(BoolKind), returns=BoolKind, domain=true)
Or = declare_function("Or", Many(BoolKind), returns=BoolKind, domain=true)
Not = declare_function("Not", BoolKind, returns=BoolKind, domain=true)
