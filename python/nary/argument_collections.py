"""A head's associative and commutative properties decide what collection its arguments form.

    associative  commutative  arguments   collection     changed by the other properties
    no           no           any         fixed tuple    never
    no           yes          two         unordered pair only when they collapse it
    no           yes          other       fixed tuple    never, only ordered
    yes          no           any         sequence       flattened, equal neighbours merge
    yes          yes          any         multiset       flattened, all equal ones merge

The steps of its other properties act on that collection until it stops shrinking.

    >>> from nary import Mul, NumberKind, log
    >>> from nary import arithmetic_rules
    >>> x, one = NumberKind("x"), Mul.kind.output(1)
    >>> normalise_collection(Mul, [x, Mul(one, x)], lambda e: True)
    Mul(x, x)
    >>> normalise_collection(Mul, [log(x), Mul.kind.output(0)], lambda e: False)
    Mul(0, log(x))
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, NamedTuple

from ._core import Expr
from .properties import is_property

__all__ = ["acting_properties", "collection_step", "count_step", "normalise_collection"]


def normalise_collection(
    head: Expr, args: list[Expr], has_a_value: Callable[[Expr], bool],
) -> Expr:
    associative, commutative = _declares(head, "is_associative"), _declares(head, "is_commutative")
    if associative:
        runs = _merged(_runs(_flattened(head, args)), commutative)
        return _rebuilt(head, _apply_steps(head, runs, has_a_value))
    if commutative and len(args) == 2:
        runs = _merged(_runs(args), commutative=True)
        return _rebuilt_if_collapsed(head, args, _apply_steps(head, runs, has_a_value))
    if commutative:
        return head(*sorted(args, key=_order_key))
    return head(*args)


@dataclass
class Run:
    arg: Expr
    count: int


def _flattened(head: Expr, args: list[Expr]) -> Iterable[Expr]:
    for arg in args:
        if arg.head == head:
            yield from arg.args
        else:
            yield arg


def _runs(args: Iterable[Expr]) -> list[Run]:
    return [Run(arg, 1) for arg in args]


def _merged(runs: list[Run], commutative: bool) -> list[Run]:
    """Equal arguments share a run: any two if the head is commutative, else only neighbours.

    >>> from nary import NumberKind
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> _merged(_runs([x, y, x, x]), commutative=True)
    [Run(arg=x, count=3), Run(arg=y, count=1)]
    >>> _merged(_runs([x, y, x, x]), commutative=False)
    [Run(arg=x, count=1), Run(arg=y, count=1), Run(arg=x, count=2)]
    """
    merged: list[Run] = []
    by_arg: dict[Expr, Run] = {}
    for run in runs:
        if run.count == 0:
            continue
        if commutative:
            partner = by_arg.get(run.arg)
        else:
            partner = merged[-1] if merged and merged[-1].arg == run.arg else None
        if partner is None:
            partner = by_arg[run.arg] = Run(run.arg, 0)
            merged.append(partner)
        partner.count += run.count
    return merged


def _arguments(runs: list[Run]) -> list[Expr]:
    return [run.arg for run in runs for _ in range(run.count)]


def _size(runs: list[Run]) -> int:
    return sum(run.count for run in runs)


def _apply_steps(head: Expr, runs: list[Run], has_a_value: Callable) -> list[Run] | Expr:
    """Each pass applies every step once, and passes repeat only while the collection shrinks.

    >>> from nary import Mul, NumberKind
    >>> x, one = NumberKind("x"), Mul.kind.output(1)
    >>> _apply_steps(Mul, _runs([x, one, x]), lambda e: True)
    [Run(arg=x, count=2)]
    """
    while True:
        after = _apply_steps_once(head, runs, has_a_value)
        if isinstance(after, Expr) or _size(after) >= _size(runs):
            return after
        runs = after


def _apply_steps_once(head: Expr, runs: list[Run], has_a_value: Callable) -> list[Run] | Expr:
    count_steps, collection_steps = _acting_steps(head)
    runs = [Run(run.arg, _new_count(head, run, count_steps, has_a_value)) for run in runs]
    for name in collection_steps:
        args = _steps[name].function(head, _arguments(runs), has_a_value, *_parameters(head, name))
        if isinstance(args, Expr):
            return args
        runs = _runs(args)
    return _merged(runs, _declares(head, "is_commutative"))


def _new_count(head: Expr, run: Run, names: list[str], has_a_value: Callable) -> int:
    """No count step erases an argument that is not known to have a value.

    >>> from nary import Mul, NumberKind, log
    >>> x, one = NumberKind("x"), Mul.kind.output(1)
    >>> _new_count(Mul, Run(one, 2), ["identity_element"], lambda e: True)
    0
    >>> _new_count(Mul, Run(log(x), 2), ["identity_element"], lambda e: False)
    2
    """
    count = run.count
    for name in names:
        count = _steps[name].function(run.arg, count, *_parameters(head, name))
    if count == 0 and not has_a_value(run.arg):
        return run.count
    return count


def _parameters(head: Expr, name: str) -> tuple:
    return () if name.startswith("is_") else (getattr(head, name),)


def _rebuilt(head: Expr, outcome: list[Run] | Expr) -> Expr:
    if isinstance(outcome, Expr):
        return outcome
    args = _arguments(outcome)
    if _declares(head, "is_commutative"):
        args.sort(key=_order_key)
    if not args and _property(head, "identity_element") is not None:
        return _property(head, "identity_element")
    return args[0] if len(args) == 1 else head(*args)


def _rebuilt_if_collapsed(head: Expr, args: list[Expr], outcome: list[Run] | Expr) -> Expr:
    """A pair takes its steps' outcome only if it collapsed: g(a, e) = a, g(a, a) = a, g(a, z) = z need no associativity.

    >>> from nary import Add, NumberKind
    >>> x, y, zero = NumberKind("x"), NumberKind("y"), Add.kind.output(0)
    >>> _rebuilt_if_collapsed(Add, [y, x], [Run(x, 1)])
    x
    >>> _rebuilt_if_collapsed(Add, [y, x], [Run(x, 1), Run(zero, 1)])
    Add(x, y)
    """
    if isinstance(outcome, Expr):
        return outcome
    remaining = _arguments(outcome)
    if len(remaining) == 1:
        return remaining[0]
    if not remaining and _property(head, "identity_element") is not None:
        return _property(head, "identity_element")
    return head(*sorted(args, key=_order_key))


def _order_key(e: Expr) -> tuple:
    """Some fixed order of expressions, which is unspecified and may change.

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


def _property(head: Expr, name: str) -> object:
    """A property's value, or None for a head that is not a declared function and so has none."""
    return getattr(head, name, None)


def _declares(head: Expr, name: str) -> bool:
    value = _property(head, name)
    return value is not None and value is not False


_acting: dict[Expr, tuple[list[str], list[str]]] = {}


def _acting_steps(head: Expr) -> tuple[list[str], list[str]]:
    """The count steps and the collection steps that act on a head; only a declared head has any, so only those are cached.

    >>> from nary import Mul
    >>> _acting_steps(Mul)
    (['identity_element'], ['absorbing_element'])
    """
    if head in _acting:
        return _acting[head]
    associative, commutative = _declares(head, "is_associative"), _declares(head, "is_commutative")
    acting = [
        name for name in _steps
        if _declares(head, name) and (commutative or associative and not _steps[name].multiset_only)
    ]
    steps = [n for n in acting if _steps[n].on_counts], [n for n in acting if not _steps[n].on_counts]
    if acting:
        _acting[head] = steps
    return steps


def acting_properties(head: Expr) -> list[str]:
    """The properties of a head whose steps act on its arguments.

    >>> from nary.logic import Or
    >>> from nary import logic_rules
    >>> acting_properties(Or)
    ['identity_element', 'is_idempotent', 'absorbing_element']
    """
    count_steps, collection_steps = _acting_steps(head)
    return count_steps + collection_steps


class Step(NamedTuple):
    function: Callable
    on_counts: bool
    multiset_only: bool


_steps: dict[str, Step] = {}


def count_step(name: str) -> Callable:
    """A count step gives an argument's new count, and is sound for a sequence and a multiset alike.

    >>> _steps["is_idempotent"].function(None, 3)
    1
    """
    return _register(name, on_counts=True, multiset_only=False)


def collection_step(name: str, multiset_only: bool = False) -> Callable:
    """A collection step gives new arguments, or the result, from all of them.

    >>> from nary import NumberKind
    >>> x, zero = NumberKind("x"), NumberKind(0)
    >>> _steps["absorbing_element"].function(None, [x, zero], lambda e: True, zero)
    0
    """
    return _register(name, on_counts=False, multiset_only=multiset_only)


def _register(name: str, on_counts: bool, multiset_only: bool) -> Callable:
    if not is_property(name):
        raise ValueError(f"{name} is not a property")

    def register(function: Callable) -> Callable:
        if name in _steps:
            raise ValueError(f"{name} already has a step")
        _steps[name] = Step(function, on_counts, multiset_only)
        _acting.clear()
        return function

    return register


@count_step("identity_element")
def _drop_the_unit(arg: Expr, count: int, unit: Expr) -> int:
    return 0 if arg == unit else count


@count_step("is_idempotent")
def _keep_one(arg: Expr, count: int) -> int:
    return min(count, 1)


@collection_step("absorbing_element")
def _absorb(head: Expr, args: list[Expr], has_a_value: Callable, zero: Expr) -> list[Expr] | Expr:
    if zero in args and all(has_a_value(arg) for arg in args if arg != zero):
        return zero
    return args
