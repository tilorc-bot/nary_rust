"""A head's associative and commutative laws decide what collection its arguments form.

    associative  commutative  arguments   collection     changed by the other laws
    no           no           any         fixed tuple    never
    no           yes          two         unordered pair only when they collapse it
    no           yes          other       fixed tuple    never, only ordered
    yes          no           any         sequence       flattened, equal neighbours merge
    yes          yes          any         multiset       flattened, all equal ones merge

Every other law acts on that collection until it stops shrinking.

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
from ._identities import Law, absorbing, associative, commutative, idempotent, identities, identity

__all__ = ["acting_laws", "collection_step", "count_step", "normalise_collection"]


def normalise_collection(
    head: Expr, args: list[Expr], has_a_value: Callable[[Expr], bool],
) -> Expr:
    shape = _shape(head)
    if shape.associative:
        runs = _merged(_runs(_flattened(head, args)), shape.commutative)
        return _rebuilt(head, _apply_laws(head, runs, shape, has_a_value), shape)
    if shape.commutative and len(args) == 2:
        runs = _merged(_runs(args), commutative=True)
        outcome = _apply_laws(head, runs, shape, has_a_value)
        return _rebuilt_if_collapsed(head, args, outcome, shape)
    if shape.commutative:
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
    for run in runs:
        if run.count == 0:
            continue
        partners = merged if commutative else merged[-1:]
        partner = next((other for other in partners if other.arg == run.arg), None)
        if partner is None:
            merged.append(Run(run.arg, run.count))
        else:
            partner.count += run.count
    return merged


def _arguments(runs: list[Run]) -> list[Expr]:
    return [run.arg for run in runs for _ in range(run.count)]


def _size(runs: list[Run]) -> int:
    return sum(run.count for run in runs)


def _apply_laws(head: Expr, runs: list[Run], shape: Shape, has_a_value: Callable) -> list[Run] | Expr:
    """Each pass applies every law once, and passes repeat only while the collection shrinks.

    >>> from nary import Mul, NumberKind
    >>> x, one = NumberKind("x"), Mul.kind.output(1)
    >>> _apply_laws(Mul, _runs([x, one, x]), _shape(Mul), lambda e: True)
    [Run(arg=x, count=2)]
    """
    while True:
        after = _apply_laws_once(head, runs, shape, has_a_value)
        if isinstance(after, Expr) or _size(after) >= _size(runs):
            return after
        runs = after


def _apply_laws_once(head: Expr, runs: list[Run], shape: Shape, has_a_value: Callable) -> list[Run] | Expr:
    runs = [Run(run.arg, _new_count(run, shape.count_laws, has_a_value)) for run in runs]
    for law in shape.collection_laws:
        args = _steps[law.of].function(head, _arguments(runs), has_a_value, *law.args or ())
        if isinstance(args, Expr):
            return args
        runs = _runs(args)
    return _merged(runs, shape.commutative)


def _new_count(run: Run, count_laws: list[Law], has_a_value: Callable) -> int:
    """No count law erases an argument that is not known to have a value.

    >>> from nary import NumberKind, log
    >>> x = NumberKind("x")
    >>> _new_count(Run(log(x), 2), [identity(log(x))], lambda e: False)
    2
    >>> _new_count(Run(x, 2), [identity(x)], lambda e: True)
    0
    """
    count = run.count
    for law in count_laws:
        count = _steps[law.of].function(run.arg, count, *law.args or ())
    if count == 0 and not has_a_value(run.arg):
        return run.count
    return count


def _rebuilt(head: Expr, outcome: list[Run] | Expr, shape: Shape) -> Expr:
    if isinstance(outcome, Expr):
        return outcome
    args = _arguments(outcome)
    if shape.commutative:
        args.sort(key=_order_key)
    if not args and shape.unit is not None:
        return shape.unit
    return args[0] if len(args) == 1 else head(*args)


def _rebuilt_if_collapsed(head: Expr, args: list[Expr], outcome: list[Run] | Expr, shape: Shape) -> Expr:
    """A pair takes its laws' outcome only if it collapsed: g(a, e) = a, g(a, a) = a, g(a, z) = z need no associativity.

    >>> from nary import Add, NumberKind
    >>> x, y, zero = NumberKind("x"), NumberKind("y"), Add.kind.output(0)
    >>> _rebuilt_if_collapsed(Add, [y, x], [Run(x, 1)], _shape(Add))
    x
    >>> _rebuilt_if_collapsed(Add, [y, x], [Run(x, 1), Run(zero, 1)], _shape(Add))
    Add(x, y)
    """
    if isinstance(outcome, Expr):
        return outcome
    remaining = _arguments(outcome)
    if len(remaining) == 1:
        return remaining[0]
    if not remaining and shape.unit is not None:
        return shape.unit
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


class Shape(NamedTuple):
    associative: bool
    commutative: bool
    unit: Expr | None
    count_laws: list[Law]
    collection_laws: list[Law]


_shapes: dict[Expr, Shape] = {}


def _shape(head: Expr) -> Shape:
    """
    >>> from nary import Mul
    >>> _shape(Mul).associative, _shape(Mul).commutative, _shape(Mul).unit
    (True, True, 1)
    >>> _shape(Mul).count_laws, _shape(Mul).collection_laws
    ([identity(1)], [absorbing(0)])
    """
    if head in _shapes:
        return _shapes[head]
    laws = [law for law in identities(head) if isinstance(law, Law)]
    generic = {law.of for law in laws}
    is_associative, is_commutative = associative in generic, commutative in generic
    plain = [law for law in laws if law.when is None]
    units = [law.args[0] for law in plain if law.of is identity]
    acting = [law for law in plain if law.of in _steps] if is_associative or is_commutative else []
    acting = [law for law in acting if is_commutative or not _steps[law.of].multiset_only]
    shape = Shape(
        is_associative,
        is_commutative,
        units[0] if units else None,
        [law for law in acting if _steps[law.of].on_counts],
        [law for law in acting if not _steps[law.of].on_counts],
    )
    if laws:
        _shapes[head] = shape
    return shape


def acting_laws(head: Expr) -> list[Law]:
    """The laws of a head whose steps act on its arguments, as its block lists them.

    >>> from nary.logic import Or
    >>> from nary import logic_rules
    >>> acting_laws(Or)
    [identity(false), absorbing(true), idempotent]
    """
    shape = _shape(head)
    acting = shape.count_laws + shape.collection_laws
    return [law for law in identities(head) if law in acting]


class Step(NamedTuple):
    function: Callable
    on_counts: bool
    multiset_only: bool


_steps: dict[Law, Step] = {}


def count_step(law: Law) -> Callable:
    """A count step gives an argument's new count, and is sound for a sequence and a multiset alike.

    >>> _steps[idempotent].function(None, 3)
    1
    """
    return _register(law, on_counts=True, multiset_only=False)


def collection_step(law: Law, multiset_only: bool = False) -> Callable:
    """A collection step gives new arguments, or the result, from all of them.

    >>> from nary import NumberKind
    >>> x, zero = NumberKind("x"), NumberKind(0)
    >>> _steps[absorbing].function(None, [x, zero], lambda e: True, zero)
    0
    """
    return _register(law, on_counts=False, multiset_only=multiset_only)


def _register(law: Law, on_counts: bool, multiset_only: bool) -> Callable:
    def register(function: Callable) -> Callable:
        if law in _steps:
            raise ValueError(f"{law!r} already has a step")
        _steps[law] = Step(function, on_counts, multiset_only)
        _shapes.clear()
        return function

    return register


@count_step(identity)
def _drop_the_unit(arg: Expr, count: int, unit: Expr) -> int:
    return 0 if arg == unit else count


@count_step(idempotent)
def _keep_one(arg: Expr, count: int) -> int:
    return min(count, 1)


@collection_step(absorbing)
def _absorb(head: Expr, args: list[Expr], has_a_value: Callable, zero: Expr) -> list[Expr] | Expr:
    if zero in args and all(has_a_value(arg) for arg in args if arg != zero):
        return zero
    return args
