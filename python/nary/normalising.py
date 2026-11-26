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
from ._identities import (
    Law, absorbing, associative, commutative, idempotent, identities, identity, involution,
    left_absorbing, right_identity,
)
from .functions import is_lambda
from .kinds import Many
from .logic import true
from .rewriting import _has_a_value

__all__ = ["normalise"]


def normalise(e: Expr, known: Callable[[Expr], object] | None = None) -> Expr:
    if not isinstance(e, Expr):
        raise TypeError(f"normalise expects an expression, got {e!r}")
    known = known or (lambda condition: False)
    done = {}

    def normal(e: Expr) -> Expr:
        if e.is_atom or is_lambda(e):
            return e
        if e not in done:
            done[e] = _node(normal(e.head), [normal(arg) for arg in e.args], has_a_value)
        return done[e]

    def holds(condition: Expr) -> bool:
        condition = normal(condition)
        return condition == true or known(condition) is True

    def has_a_value(e: Expr) -> bool:
        return _has_a_value(e, holds)

    return normal(e)


def _node(head: Expr, args: list[Expr], has_a_value: Callable[[Expr], bool]) -> Expr:
    laws = {item.of: item for item in identities(head)}
    for law, step in _STEPS:
        if law in laws:
            params = [_element(head, p) for p in laws[law].args or ()]
            checks = (has_a_value,) if law in _ERASING else ()
            result = step(head, args, *params, *checks)
            if isinstance(result, Expr):
                return result
            args = result
    return head(*args)


def _element(head: Expr, value: Expr | int) -> Expr:
    return value if isinstance(value, Expr) else head.kind.output(value)


def _key(e: Expr) -> tuple:
    if e.is_literal:
        return 0, type(e.value).__name__, e.value
    if e.is_constant:
        return 1, e.name
    if e.is_symbol:
        return 2, e.name, e.kind.name
    return 3, _key(e.head), tuple(_key(arg) for arg in e.args)


def _flatten(head: Expr, args: list[Expr]) -> list[Expr]:
    """
    >>> from nary import Add, NumberKind
    >>> x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
    >>> _flatten(Add, [x, Add(y, z)])
    [x, y, z]
    """
    return [part for arg in args for part in (arg.args if arg.head == head else (arg,))]


def _sort(head: Expr, args: list[Expr]) -> list[Expr]:
    """
    >>> from nary import Add, NumberKind, pi, sin
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> _sort(Add, [sin(x), y, pi, x, Add.kind.output(2)])
    [2, pi, x, y, sin(x)]
    """
    return sorted(args, key=_key)


def _drop_duplicates(head: Expr, args: list[Expr]) -> list[Expr]:
    """
    >>> from nary import BoolKind
    >>> from nary.logic import And
    >>> p, q = BoolKind("p"), BoolKind("q")
    >>> _drop_duplicates(And, [p, q, p])
    [p, q]
    """
    return [arg for i, arg in enumerate(args) if arg not in args[:i]]


def _absorb(
    head: Expr, args: list[Expr], z: Expr, has_a_value: Callable[[Expr], bool],
) -> list[Expr] | Expr:
    """
    >>> from nary import Mul, NumberKind, log
    >>> x, zero = NumberKind("x"), Mul.kind.output(0)
    >>> _absorb(Mul, [x, zero], zero, lambda e: True)
    0
    >>> _absorb(Mul, [log(x), zero], zero, lambda e: False)
    [log(x), 0]
    """
    if z in args and all(has_a_value(arg) for arg in args if arg != z):
        return z
    return args


def _absorb_left(
    head: Expr, args: list[Expr], z: Expr, has_a_value: Callable[[Expr], bool],
) -> list[Expr] | Expr:
    """
    >>> from nary import NumberKind, Pow
    >>> x, one = NumberKind("x"), Pow.kind.output(1)
    >>> _absorb_left(Pow, [one, x], one, lambda e: True)
    1
    >>> _absorb_left(Pow, [x, one], one, lambda e: True)
    [x, 1]
    """
    if len(args) == 2 and args[0] == z and has_a_value(args[1]):
        return z
    return args


def _drop_units(head: Expr, args: list[Expr], unit: Expr) -> list[Expr] | Expr:
    """
    >>> from nary import Add, NumberKind
    >>> x, y, zero = NumberKind("x"), NumberKind("y"), Add.kind.output(0)
    >>> _drop_units(Add, [x, zero, y], zero), _drop_units(Add, [zero, x], zero)
    ([x, y], x)
    >>> _drop_units(Add, [zero], zero)
    0
    """
    inputs = head.kind.inputs
    if not inputs or inputs[-1].family is not Many:
        return args
    kept = [arg for arg in args if arg != unit]
    if len(kept) < 2:
        return kept[0] if kept else unit
    return kept


def _drop_right_unit(head: Expr, args: list[Expr], unit: Expr) -> list[Expr] | Expr:
    """
    >>> from nary import NumberKind, Pow
    >>> x, one = NumberKind("x"), Pow.kind.output(1)
    >>> _drop_right_unit(Pow, [x, one], one), _drop_right_unit(Pow, [one, x], one)
    (x, [1, x])
    """
    return args[0] if len(args) == 2 and args[1] == unit else args


def _cancel(head: Expr, args: list[Expr]) -> list[Expr] | Expr:
    """
    >>> from nary import BoolKind
    >>> from nary.logic import Not
    >>> p = BoolKind("p")
    >>> _cancel(Not, [Not(p)]), _cancel(Not, [p])
    (p, [p])
    """
    (arg,) = args
    return arg.args[0] if arg.head == head else args


_ERASING = {absorbing, left_absorbing}

_STEPS: list[tuple[Law, Callable[..., list[Expr] | Expr]]] = [
    (associative, _flatten),
    (commutative, _sort),
    (idempotent, _drop_duplicates),
    (absorbing, _absorb),
    (left_absorbing, _absorb_left),
    (identity, _drop_units),
    (right_identity, _drop_right_unit),
    (involution, _cancel),
]
