from __future__ import annotations

from typing import Callable

from ._core import Expr
from ._identities import (
    Law, absorbing, associative, commutative, idempotent, identities, identity, involution,
    left_absorbing, right_identity,
)
from .kinds import Many

__all__ = ["apply_laws"]


def apply_laws(head: Expr, args: list[Expr], has_a_value: Callable[[Expr], bool]) -> Expr:
    """
    >>> from nary import NumberKind, Pow, arithmetic_rules
    >>> x, one = NumberKind("x"), Pow.kind.output(1)
    >>> apply_laws(Pow, [x, one], lambda e: True), apply_laws(Pow, [one, x], lambda e: False)
    (x, Pow(1, x))
    """
    laws = {item.of: item for item in identities(head)}
    for law, step in _STEPS:
        if law in laws:
            checks = (has_a_value,) if law in _ERASING else ()
            result = step(head, args, *(laws[law].args or ()), *checks)
            if isinstance(result, Expr):
                return result
            args = result
    return head(*args)


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
