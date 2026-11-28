"""print shows an expression as it reads; repr keeps the structural form.

    >>> from nary import NumberKind, Pow
    >>> x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
    >>> e = x + y * z**2 < 1
    >>> print(e)
    x + y*z**2 < 1
    >>> e
    Lt(Add(x, Mul(y, Pow(z, 2))), 1)

A product with negative powers is a fraction, and a term times -1 is subtracted.

    >>> print(3 * Pow(2, -1))
    3/2
    >>> print(x / (y + 1) - y**-2 * z)
    x/(y + 1) - z/y**2

A head the printer does not know is printed as a call.

    >>> from nary import Lambda, sin
    >>> from nary.calculus import Derivative, Integral
    >>> print(Integral(Lambda(x, sin(x)**2), 0, Derivative(sin)(y)))
    Integral(lambda x: sin(x)**2, 0, Derivative(sin)(y))

A head prints as an operator once it has an entry in NOTATIONS.

    >>> from nary import declare_function
    >>> from nary.logic import true
    >>> from nary.printing import NOTATIONS, PRODUCT, infix
    >>> Dot = declare_function("Dot", NumberKind, NumberKind, returns=NumberKind, domain=true)
    >>> NOTATIONS[Dot] = infix(" . ", PRODUCT)
    >>> print(Dot(x, y + 1))
    x . (y + 1)
"""

from . import logic, matrices, relational
from ._core import Expr
from .arithmetic import Add, Mul, Pow
from .functions import is_lambda

__all__ = ["NOTATIONS", "infix", "readable"]

LAMBDA, LOGIC, NOT, RELATION, SUM, PRODUCT, NEGATION, POWER, ATOM = range(9)


def readable(e):
    return _print(e)[0]


def _print(e):
    if e.is_symbol or e.is_constant:
        return e.name, ATOM
    if e.is_literal:
        text = repr(e.value)
        return text, NEGATION if text.startswith("-") else ATOM
    if is_lambda(e):
        *variables, body = e.args
        return f"lambda {', '.join(v.name for v in variables)}: {readable(body)}", LAMBDA
    notation = NOTATIONS.get(e.head, _call)
    return notation(e)


def _wrap(e, precedence):
    text, own = _print(e)
    return f"({text})" if own < precedence else text


def _call(e):
    return f"{_wrap(e.head, ATOM)}({', '.join(readable(a) for a in e.args)})", ATOM


def _operands(e):
    for a in e.args:
        if a.head == e.head:
            yield from _operands(a)
        else:
            yield a


def infix(operator, precedence):
    def notation(e):
        operands = list(_operands(e))
        if len(operands) < 2:
            return _call(e)
        return operator.join(_wrap(a, precedence + 1) for a in operands), precedence
    return notation


def _negated(e):
    if e.is_literal:
        return [e.kind(-e.value)] if e.value < 0 else None
    factors = list(_operands(e)) if e.head == Mul else []
    if len(factors) < 2 or not factors[0].is_literal or factors[0].value >= 0:
        return None
    first, *rest = factors
    return rest if first.value == -1 else [first.kind(-first.value), *rest]


def _product(factors):
    numerator, denominator = [], []
    for factor in factors:
        negated = _negated(factor.args[1]) if factor.head == Pow else None
        if negated is None:
            numerator.append(factor)
            continue
        base = factor.args[0]
        exponent = negated[0] if len(negated) == 1 else Mul(*negated)
        denominator.append(base if exponent.value == 1 else Pow(base, exponent))
    text = "*".join(_wrap(f, POWER) for f in numerator) or "1"
    if not denominator:
        return text, POWER if len(numerator) == 1 else PRODUCT
    below = "*".join(_wrap(f, POWER) for f in denominator)
    return f"{text}/{below if len(denominator) == 1 else f'({below})'}", PRODUCT


def _sum(e):
    terms = list(_operands(e))
    if len(terms) < 2:
        return _call(e)
    first, *rest = terms
    parts = [_wrap(first, SUM + 1)]
    for term in rest:
        negated = _negated(term)
        if negated is None:
            parts.append(f" + {_wrap(term, SUM + 1)}")
        else:
            parts.append(f" - {_product(negated)[0]}")
    return "".join(parts), SUM


def _mul(e):
    factors = list(_operands(e))
    if len(factors) < 2:
        return _call(e)
    negated = _negated(e)
    if negated is None:
        return _product(factors)
    text, precedence = _product(negated)
    return f"-{text}", NEGATION if precedence == POWER else PRODUCT


_HALF = Pow(2, -1)


def _pow(e):
    base, exponent = e.args
    if _negated(exponent) is not None:
        return _product([e])
    if exponent == _HALF:
        return f"sqrt({readable(base)})", ATOM
    return f"{_wrap(base, ATOM)}**{_wrap(exponent, POWER)}", POWER


def _not(e):
    return f"not {_wrap(e.args[0], NOT)}", NOT


NOTATIONS = {
    Add: _sum,
    Mul: _mul,
    Pow: _pow,
    relational.Eq: infix(" == ", RELATION),
    relational.Ne: infix(" != ", RELATION),
    relational.Lt: infix(" < ", RELATION),
    relational.Le: infix(" <= ", RELATION),
    relational.Gt: infix(" > ", RELATION),
    relational.Ge: infix(" >= ", RELATION),
    logic.And: infix(" and ", LOGIC),
    logic.Or: infix(" or ", LOGIC),
    logic.Not: _not,
    matrices.MatAdd: infix(" + ", SUM),
    matrices.MatMul: infix("*", PRODUCT),
}

Expr.__str__ = readable
