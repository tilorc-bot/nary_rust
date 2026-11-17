"""Integrals, sums, products, antiderivatives, derivatives, limits and
substitution.

Every function here takes a variable, declared as ``Symbol(NumberKind)`` so
that only a symbol is accepted in that position, not any NumberKind
expression. All the arguments and all the results are NumberKind.

What is bound where, as recorded with ``binds=``:

- ``Integral(body, var, lower, upper)``, ``Sum(...)`` and ``Product(...)``:
  ``var`` is bound in ``body`` only. The limits are outside its scope, so the
  ``x`` in ``Integral(f, x, 0, x)``'s upper limit is the free ``x``.
- ``Limit(expr, var, point)`` and ``Subs(expr, var, value)``: ``var`` is
  bound in ``expr``, not in ``point`` or ``value``.
- ``Antiderivative(body, var)`` and ``Derivative(expr, var)``: ``var`` stays
  free, since the result still depends on it.

Nothing reads ``binds`` yet. It is there so that substitution, when it is
written, can tell that ``x`` in the body of an integral is not the ``x``
outside it.

Several variables are written by nesting:
``Integral(Integral(f, x, a, b), y, c, d)``. There are no integers yet, so
limits such as 0, 1 or infinity are written with symbols:
``Sum(f, n, NumberKind("a"), NumberKind("b"))``.

This module is not re-exported from ``nary``; import it as ``nary.calculus``.
"""

from ._core import Symbol, function
from .kinds import NumberKind

__all__ = [
    "Antiderivative", "Derivative", "Integral", "Limit", "Product", "Subs",
    "Sum",
]

_var = Symbol(NumberKind)
_range = ("body", "var", "lower", "upper")

Integral = function(
    "Integral", NumberKind, _var, NumberKind, NumberKind,
    returns=NumberKind, names=_range, binds={1: (0,)},
)
Sum = function(
    "Sum", NumberKind, _var, NumberKind, NumberKind,
    returns=NumberKind, names=_range, binds={1: (0,)},
)
Product = function(
    "Product", NumberKind, _var, NumberKind, NumberKind,
    returns=NumberKind, names=_range, binds={1: (0,)},
)

Antiderivative = function(
    "Antiderivative", NumberKind, _var, returns=NumberKind, names=("body", "var")
)
Derivative = function(
    "Derivative", NumberKind, _var, returns=NumberKind, names=("expr", "var")
)

Limit = function(
    "Limit", NumberKind, _var, NumberKind,
    returns=NumberKind, names=("expr", "var", "point"), binds={1: (0,)},
)
# An unevaluated substitution of value for var in expr.
Subs = function(
    "Subs", NumberKind, _var, NumberKind,
    returns=NumberKind, names=("expr", "var", "value"), binds={1: (0,)},
)
