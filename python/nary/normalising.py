"""normalise applies the steps of the properties that act on each head's arguments, from the leaves up.

    >>> from nary import BoolKind, NumberKind, Pow, log, sin
    >>> from nary.logic import And, Not, Or, false, true
    >>> from nary.normalising import normalise
    >>> x, y, p, q = NumberKind("x"), NumberKind("y"), BoolKind("p"), BoolKind("q")
    >>> normalise(y + (x + 0) + x * 1), normalise(Pow(y * (2 * x) * 1, 1))
    (Add(Mul(2, x), y), Pow(Mul(2, x, y), 1))
    >>> normalise(And(q, Or(p, false), q, true)), normalise(Not(Not(p)))
    (And(p, q), Not(Not(p)))
    >>> normalise(sin(x) * 0), normalise(log(x) * 0)
    (0, Mul(0, log(x)))
    >>> normalise(NumberKind(3) / 2 + 1), normalise(Pow(2, 3) < 9), normalise(x + 1 + 2)
    (Rational(5, 2), true, Add(3, x))
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

from . import arithmetic_rules, logic_rules  # noqa: F401
from ._core import Expr
from .domains import domain_of
from .functions import is_lambda
from .property_steps import apply_property_steps
from .logic import true
from .rewriting import _has_a_value
from .traversal import bottom_up

__all__ = ["normalise"]


def normalise(e: Expr, known: Callable[[Expr], object] | None = None) -> Expr:
    """Rewrite e using the properties of the functions in it, such as Add.identity_element.

    Args:
        e: The expression to rewrite.
        known: Called as known(condition). Where it returns True, an argument that has a
            value only if condition holds may be removed.

    Returns:
        The rewritten expression.

    >>> from nary import Ne, NumberKind, log
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> normalise((y + 0) + (x + y) * 1)
    Add(Mul(2, y), x)
    >>> normalise(log(x) * 0), normalise(log(x) * 0, lambda condition: condition == Ne(x, 0))
    (Mul(0, log(x)), 0)
    """
    if not isinstance(e, Expr):
        raise TypeError(f"normalise expects an expression, got {e!r}")
    known = known or (lambda condition: False)

    walk = bottom_up(
        lambda head, args: apply_property_steps(head, args, has_a_value, walk),
        flat=lambda head: head.is_associative,
    )

    def holds(condition: Expr, assumed: set[Expr]) -> bool:
        condition = walk(condition)
        return condition == true or condition in assumed or known(condition) is True

    def has_a_value(e: Expr, wherever_these_have_values: list[Expr]) -> bool:
        assumed = {walk(domain) for domain in _domains_inside(wherever_these_have_values)}
        return _has_a_value(e, lambda condition: holds(condition, assumed))

    return walk(e)


def _domains_inside(es: list[Expr]) -> Iterator[Expr]:
    """The domains of es and of everything inside them that has a value wherever they do.

    >>> from nary import NumberKind, Pow, log, sin
    >>> from nary.functions import Lambda
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> list(_domains_inside([sin(log(x)), Pow(y, -1)]))
    [true, Ne(x, 0), Or(Ne(y, 0), Gt(re(-1), 0))]
    >>> list(_domains_inside([Lambda(y, log(y))(x)]))
    []
    """
    for e in es:
        if e.is_atom or is_lambda(e) or not e.head.is_constant:
            continue
        domain = domain_of(e)
        if domain is not None:
            yield domain
            yield from _domains_inside(e.args)
