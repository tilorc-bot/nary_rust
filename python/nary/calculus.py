"""Calculus of functions of one number.

Every function here takes a function, not a body and a variable. A variable
is bound only by ``Lambda``, so the function can be a lambda, a declared
function such as ``sin``, or an unknown function, a symbol of a function
kind. With ``NumberFunction = FunctionKind((NumberKind,), NumberKind)``,
this module declares:

- ``Integral(integrand, lower, upper)``, ``Sum(summand, lower, upper)`` and
  ``Product(factor, lower, upper)``: a ``NumberFunction`` and two numbers,
  returning a number.
- ``Limit(function, point)``: a ``NumberFunction`` and a number, returning
  a number.
- ``Derivative(function)`` and ``Antiderivative(function)``: a
  ``NumberFunction``, returning a ``NumberFunction``. So ``Derivative(f)(a)``
  is the derivative of ``f`` at ``a``, and ``Derivative(Derivative(f))`` is
  the second derivative.

There is no ``Subs``: a substitution left unevaluated is the application of
a lambda, ``Lambda(x, expr)(value)``.

The module is imported as ``nary.calculus``; ``import nary`` does not
import it, and its names are not re-exported from ``nary``.

    >>> from nary import Lambda, NumberKind, sin
    >>> from nary.calculus import Derivative, Integral, Limit, NumberFunction
    >>> x, a, b = NumberKind("x"), NumberKind("a"), NumberKind("b")
    >>> f = NumberFunction("f")
    >>> Integral(Lambda(x, x * x), a, b)
    Integral(Lambda(x, Mul(x, x)), a, b)
    >>> Integral(sin, a, b).integrand, Integral(f, a, b).kind
    (sin, NumberKind)
    >>> Derivative(f)(a), Derivative(Derivative(f)).kind
    (Derivative(f)(a), FunctionKind((NumberKind,), NumberKind))
    >>> Limit(Lambda(x, sin(x) * x), a)
    Limit(Lambda(x, Mul(sin(x), x)), a)
    >>> Lambda(x, sin(x))(a)                 # a substitution, unevaluated
    Lambda(x, sin(x))(a)
    >>> Integral(x * x, a, b)
    Traceback (most recent call last):
        ...
    TypeError: Integral expects FunctionKind((NumberKind,), NumberKind), got NumberKind: Mul(x, x)

Known gaps:

- A limit has no direction: there is no limit from the left or the right.
- Only functions of one number. There are no partial derivatives, and a
  lambda of two variables is not accepted.
- ``Sum`` and ``Product`` do not say whether the upper bound is included.
- Nothing is evaluated: no integral, sum, product, limit or derivative is
  ever computed or simplified.
"""

from ._core import FunctionKind
from .domains import declare_function
from .kinds import NumberKind

__all__ = [
    "NumberFunction",
    "Integral", "Sum", "Product", "Limit", "Derivative", "Antiderivative",
]

NumberFunction = FunctionKind((NumberKind,), NumberKind)

# No domain is stated (domain=None): an integral, sum, product, limit or
# derivative need not exist, and when it does is not written down yet.
Integral = declare_function(
    "Integral", NumberFunction, NumberKind, NumberKind,
    returns=NumberKind, names=("integrand", "lower", "upper"), domain=None,
)
Sum = declare_function(
    "Sum", NumberFunction, NumberKind, NumberKind,
    returns=NumberKind, names=("summand", "lower", "upper"), domain=None,
)
Product = declare_function(
    "Product", NumberFunction, NumberKind, NumberKind,
    returns=NumberKind, names=("factor", "lower", "upper"), domain=None,
)
Limit = declare_function(
    "Limit", NumberFunction, NumberKind,
    returns=NumberKind, names=("function", "point"), domain=None,
)
Derivative = declare_function(
    "Derivative", NumberFunction,
    returns=NumberFunction, names=("function",), domain=None,
)
Antiderivative = declare_function(
    "Antiderivative", NumberFunction,
    returns=NumberFunction, names=("function",), domain=None,
)
