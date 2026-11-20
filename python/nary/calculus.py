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
from .logic import true

__all__ = [
    "NumberFunction",
    "Integral", "Sum", "Product", "Limit", "Derivative", "Antiderivative",
]

NumberFunction = FunctionKind((NumberKind,), NumberKind)

# The parameters, which name the arguments: Integral(sin, 0, x).integrand.
integrand, summand = NumberFunction("integrand"), NumberFunction("summand")
factor, function = NumberFunction("factor"), NumberFunction("function")
lower, upper, point = NumberKind("lower"), NumberKind("upper"), NumberKind("point")

# AWAITING A DECISION (see nary.domains): when an integral, sum, product or
# limit has a value cannot be written yet, so these four have domain=None.
Integral = declare_function("Integral", integrand, lower, upper, returns=NumberKind, domain=None)
Sum = declare_function("Sum", summand, lower, upper, returns=NumberKind, domain=None)
Product = declare_function("Product", factor, lower, upper, returns=NumberKind, domain=None)
Limit = declare_function("Limit", function, point, returns=NumberKind, domain=None)
# A derivative or an antiderivative is always a function, though it may have
# no value at some points, as Derivative(f)(a) has none where f is not
# differentiable.
Derivative = declare_function("Derivative", function, returns=NumberFunction, domain=true)
Antiderivative = declare_function("Antiderivative", function, returns=NumberFunction, domain=true)
