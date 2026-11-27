from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterator

from ._core import Expr

__all__ = ["Commutative", "commutative_laws", "declare_commutative", "normalise_commutative"]


@dataclass(frozen=True)
class Commutative:
    unit: Expr | None = None
    zero: Expr | None = None
    idempotent: bool = False


_declared: dict[Expr, Commutative] = {}


def declare_commutative(head: Expr, laws: Commutative) -> None:
    _declared[head] = laws


def commutative_laws(head: Expr) -> Commutative | None:
    """
    >>> from nary import Add, Pow, arithmetic_rules
    >>> commutative_laws(Add), commutative_laws(Pow)
    (Commutative(unit=0, zero=None, idempotent=False), None)
    """
    return _declared.get(head)


def normalise_commutative(
    head: Expr, args: list[Expr], laws: Commutative, has_a_value: Callable[[Expr], bool],
) -> Expr:
    """
    >>> from nary import Mul, NumberKind, log
    >>> x, zero, one = NumberKind("x"), Mul.kind.output(0), Mul.kind.output(1)
    >>> laws = Commutative(unit=one, zero=zero)
    >>> normalise_commutative(Mul, [x, Mul(one, x)], laws, lambda e: True)
    Mul(x, x)
    >>> normalise_commutative(Mul, [one, one], laws, lambda e: True)
    1
    >>> normalise_commutative(Mul, [x, zero], laws, lambda e: True)
    0
    >>> normalise_commutative(Mul, [log(x), zero], laws, lambda e: False)
    Mul(0, log(x))
    >>> normalise_commutative(Mul, [x, x], Commutative(idempotent=True), lambda e: True)
    x
    """
    counts = Counter(_flattened(head, args))
    counts.pop(laws.unit, None)
    if laws.zero in counts and all(has_a_value(p) for p in counts if p != laws.zero):
        return laws.zero
    parts = list(counts) if laws.idempotent else list(counts.elements())
    if not parts and laws.unit is not None:
        return laws.unit
    if len(parts) == 1:
        return parts[0]
    return head(*sorted(parts, key=_order_key))


def _flattened(head: Expr, args: list[Expr]) -> Iterator[Expr]:
    for arg in args:
        if arg.head == head:
            yield from arg.args
        else:
            yield arg


def _order_key(e: Expr) -> tuple:
    """
    >>> from nary import Add, NumberKind, pi, sin
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> sorted([sin(x), y, pi, x, Add.kind.output(2)], key=_order_key)
    [2, pi, x, y, sin(x)]
    """
    if e.is_literal:
        return 0, type(e.value).__name__, e.value
    if e.is_constant:
        return 1, e.name
    if e.is_symbol:
        return 2, e.name, e.kind.name
    return 3, _order_key(e.head), tuple(_order_key(arg) for arg in e.args)
