"""
    >>> from nary import Mul, NumberKind, log
    >>> from nary.arithmetic_rules import mul
    >>> x, one = NumberKind("x"), Mul.kind.output(1)
    >>> normalise_commutative(Mul, [x, Mul(one, x)], lambda e: True)
    Mul(x, x)
    >>> normalise_commutative(Mul, [one, one], lambda e: True)
    1
    >>> normalise_commutative(Mul, [log(x), Mul.kind.output(0)], lambda e: False)
    Mul(0, log(x))
    >>> routine_laws(Mul)
    [identity(1), absorbing(0)]
"""

from __future__ import annotations

from collections import Counter
from typing import Callable, Iterator

from ._core import Expr
from ._identities import Law, absorbing, associative, commutative, idempotent, identities, identity

__all__ = ["law_step", "normalise_commutative", "routine_laws"]

Step = Callable[..., "Counter[Expr] | Expr"]
_steps: dict[Law, Step] = {}
_plans: dict[Expr, tuple] = {}


def law_step(law: Law) -> Callable[[Step], Step]:
    def register(step: Step) -> Step:
        if law in _steps:
            raise ValueError(f"{law!r} already has a step")
        _steps[law] = step
        _plans.clear()
        return step

    return register


def routine_laws(head: Expr) -> list[Law]:
    """A head's steps run in the order its block lists their laws.

    >>> from nary.logic import Or
    >>> from nary import logic_rules
    >>> routine_laws(Or)
    [identity(false), absorbing(true), idempotent]
    """
    return [law for law, _ in _plan(head)[1] or ()]


def normalise_commutative(
    head: Expr, args: list[Expr], has_a_value: Callable[[Expr], bool],
) -> Expr:
    unit, steps = _plan(head)
    if steps is None:
        return head(*args)
    counts = Counter(_flattened(head, args))
    for law, step in steps:
        counts = step(head, +counts, has_a_value, *law.args or ())
        if isinstance(counts, Expr):
            return counts
    parts = sorted((+counts).elements(), key=_order_key)
    if not parts and unit is not None:
        return unit
    return parts[0] if len(parts) == 1 else head(*parts)


def _plan(head: Expr) -> tuple:
    if head in _plans:
        return _plans[head]
    laws = identities(head)
    generic = {law.of for law in laws if isinstance(law, Law)}
    if not {associative, commutative} <= generic:
        plan = None, None
    else:
        plain = [law for law in laws if isinstance(law, Law) and law.when is None]
        units = [law.args[0] for law in plain if law.of is identity]
        steps = [(law, _steps[law.of]) for law in plain if law.of in _steps]
        plan = (units[0] if units else None), steps
    if laws:
        _plans[head] = plan
    return plan


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


@law_step(identity)
def _drop_unit(head: Expr, counts: Counter, has_a_value: Callable, unit: Expr) -> Counter:
    """
    >>> from nary import Add, NumberKind
    >>> x, zero = NumberKind("x"), Add.kind.output(0)
    >>> _drop_unit(Add, Counter([x, zero, zero]), None, zero)
    Counter({x: 1})
    """
    del counts[unit]
    return counts


@law_step(absorbing)
def _absorb(head: Expr, counts: Counter, has_a_value: Callable, zero: Expr) -> Counter | Expr:
    """
    >>> from nary import Mul, NumberKind, log
    >>> x, zero = NumberKind("x"), Mul.kind.output(0)
    >>> _absorb(Mul, Counter([x, zero]), lambda e: True, zero)
    0
    >>> _absorb(Mul, Counter([log(x), zero]), lambda e: False, zero)
    Counter({log(x): 1, 0: 1})
    """
    if zero in counts and all(has_a_value(p) for p in counts if p != zero):
        return zero
    return counts


@law_step(idempotent)
def _drop_repeats(head: Expr, counts: Counter, has_a_value: Callable) -> Counter:
    """
    >>> from nary import NumberKind
    >>> x = NumberKind("x")
    >>> _drop_repeats(None, Counter([x, x]), None)
    Counter({x: 1})
    """
    return Counter(list(counts))
