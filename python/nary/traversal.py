"""
    >>> from nary import NumberKind, sin
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> bottom_up(lambda head, args: head(*reversed(args)))(sin(x) + y)
    Add(y, sin(x))
"""

from __future__ import annotations

from typing import Callable

from ._core import Expr
from .functions import is_lambda

__all__ = ["bottom_up"]


def bottom_up(at_node: Callable[[Expr, list[Expr]], Expr]) -> Callable[[Expr], Expr]:
    done = {}

    def walk(e: Expr) -> Expr:
        if e.is_atom or is_lambda(e):
            return e
        if e not in done:
            done[e] = at_node(walk(e.head), [walk(arg) for arg in e.args])
        return done[e]

    return walk
