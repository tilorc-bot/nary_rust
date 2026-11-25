"""Boolean connectives and constants.

``And`` and ``Or`` take any number of ``BoolKind`` arguments and ``Not``
takes one; each returns a ``BoolKind``. ``true`` and ``false`` are
constants of ``BoolKind``, declared with ``declare_constant``: named leaves,
each equal only to itself. This module is not re-exported from ``nary``;
import it as ``nary.logic``.

    >>> import nary as nr
    >>> from nary.logic import And, Not, Or, true
    >>> x, y = nr.NumberKind("x"), nr.NumberKind("y")
    >>> And(x < y, Not(nr.Eq(x, y)), true)
    And(Lt(x, y), Not(Eq(x, y)), true)
    >>> Or(x < y, True)
    Traceback (most recent call last):
        ...
    TypeError: Or expects BoolKind, got bool: True

A Python ``True`` or ``False`` is not accepted where a ``BoolKind`` is
required, and is not converted; use ``true`` and ``false``. There are no
operators for these functions: ``&``, ``|`` and ``~`` do not build them.
"""

from ._core import declare_constant
from .domains import declare_function
from .identities import (
    absorbing, associative, commutative, declare_identities, idempotent, identity, singleton,
)
from .kinds import BoolKind

__all__ = ["And", "Not", "Or", "false", "true"]

true = declare_constant("true", BoolKind)
false = declare_constant("false", BoolKind)

And = declare_function("And", rest=BoolKind, returns=BoolKind, domain=true)
Or = declare_function("Or", rest=BoolKind, returns=BoolKind, domain=true)
Not = declare_function("Not", BoolKind, returns=BoolKind, domain=true)


# Everything that holds for each function, in one place (see nary.identities).
declare_identities(And, [
    associative, commutative, singleton, idempotent, identity(true), absorbing(false),
])
declare_identities(Or, [
    associative, commutative, singleton, idempotent, identity(false), absorbing(true),
])
