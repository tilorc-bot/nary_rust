"""normalise applies the steps of the properties that act on each head's arguments, from the leaves up.

    >>> from nary import BoolKind, NumberKind, Pow, log, sin
    >>> from nary.logic import And, Not, Or, false, true
    >>> from nary.normalising import normalise
    >>> x, y, p, q = NumberKind("x"), NumberKind("y"), BoolKind("p"), BoolKind("q")
    >>> normalise(y + (x + 0) + x * 1), normalise(Pow(y * (2 * x) * 1, 1))
    (Add(x, x, y), Pow(Mul(2, x, y), 1))
    >>> normalise(And(q, Or(p, false), q, true)), normalise(Not(Not(p)))
    (And(p, q), Not(Not(p)))
    >>> normalise(sin(x) * 0), normalise(log(x) * 0)
    (0, Mul(0, log(x)))
    >>> normalise(NumberKind(3) / 2 + 1), normalise(Pow(2, 3) < 9), normalise(x + 1 + 2)
    (Rational(5, 2), true, Add(3, x))
"""

from __future__ import annotations

from typing import Callable

from . import arithmetic_rules, logic_rules  # noqa: F401
from ._core import Expr
from .property_steps import apply_property_steps
from .logic import true
from .rewriting import _has_a_value
from .traversal import bottom_up_every_node

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
    Add(x, y, y)
    >>> normalise(log(x) * 0), normalise(log(x) * 0, lambda condition: condition == Ne(x, 0))
    (Mul(0, log(x)), 0)
    """
    return _normalise_with(bottom_up_every_node, e, known)


def _normalise_with(
    traversal: Callable, e: Expr, known: Callable[[Expr], object] | None = None,
) -> Expr:
    """
    >>> from nary import NumberKind
    >>> from nary.traversal import bottom_up
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> flattening_first = lambda at_node: bottom_up(at_node, flat=lambda head: head.is_associative)
    >>> _normalise_with(flattening_first, (y + 0) + x)
    Add(x, y)
    """
    if not isinstance(e, Expr):
        raise TypeError(f"normalise expects an expression, got {e!r}")
    known = known or (lambda condition: False)

    def literal_or_property_steps(head: Expr, args: list[Expr]) -> Expr:
        if head.evaluate_literals and not head.is_associative:
            literal = head.evaluate_literals(*args)
            if literal is not None:
                return literal
        return apply_property_steps(head, args, has_a_value)

    walk = traversal(literal_or_property_steps)

    def holds(condition: Expr) -> bool:
        condition = walk(condition)
        return condition == true or known(condition) is True

    def has_a_value(e: Expr) -> bool:
        return _has_a_value(e, holds)

    return walk(e)
