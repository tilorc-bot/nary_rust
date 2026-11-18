"""Boolean connectives and constants.

``And`` and ``Or`` take any number of ``BoolKind`` arguments and ``Not``
takes one; each returns a ``BoolKind``. ``true`` and ``false`` are constants:
functions of no arguments, already applied, so they are expressions and are
not called again. This module is not re-exported from ``nary``; import it as
``nary.logic``.

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

from ._core import function
from .kinds import BoolKind

__all__ = ["And", "Not", "Or", "false", "true"]

And = function("And", rest=BoolKind, returns=BoolKind)
Or = function("Or", rest=BoolKind, returns=BoolKind)
Not = function("Not", BoolKind, returns=BoolKind)

# A constant is a function of no arguments, applied once.
true = function("true", returns=BoolKind)()
false = function("false", returns=BoolKind)()
