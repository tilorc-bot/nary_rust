"""normalise applies the laws declared for each head, from the leaves up.

    >>> from nary import BoolKind, NumberKind, Pow, log, sin
    >>> from nary.logic import And, Not, Or, false, true
    >>> from nary.normalising import normalise
    >>> x, y, p, q = NumberKind("x"), NumberKind("y"), BoolKind("p"), BoolKind("q")
    >>> normalise(y + (x + 0) + x * 1), normalise(Pow(y * (2 * x) * 1, 1))
    (Add(x, x, y), Mul(2, x, y))
    >>> normalise(And(q, Or(p, false), q, true)), normalise(Not(Not(p)))
    (And(p, q), p)
    >>> normalise(sin(x) * 0), normalise(log(x) * 0), normalise(Pow(1, log(x)))
    (0, Mul(0, log(x)), Pow(1, log(x)))
"""

from __future__ import annotations

from typing import Callable

from . import arithmetic_rules, logic_rules  # noqa: F401
from ._core import Expr
from .law_steps import apply_laws
from .logic import true
from .rewriting import _has_a_value
from .traversal import bottom_up

__all__ = ["normalise"]


def normalise(e: Expr, known: Callable[[Expr], object] | None = None) -> Expr:
    if not isinstance(e, Expr):
        raise TypeError(f"normalise expects an expression, got {e!r}")
    known = known or (lambda condition: False)
    normal = bottom_up(lambda head, args: apply_laws(head, args, has_a_value))

    def holds(condition: Expr) -> bool:
        condition = normal(condition)
        return condition == true or known(condition) is True

    def has_a_value(e: Expr) -> bool:
        return _has_a_value(e, holds)

    return normal(e)
