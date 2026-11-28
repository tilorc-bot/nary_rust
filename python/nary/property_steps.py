from __future__ import annotations

from itertools import groupby
from typing import Callable, NamedTuple

from ._core import Expr
from .properties import is_property

__all__ = ["apply_property_steps", "step"]

_sort_key = repr


class _Step(NamedTuple):
    function: Callable
    commutative_only: bool
    per_argument: bool
    merges: bool


_step_of_property: dict[str, _Step] = {}


def step(
    name: str, commutative_only: bool = False, per_argument: bool = False, merges: bool = False,
) -> Callable:
    """Register a function that changes the arguments of a head that has the property name.

    Args:
        name: A property, already declared with declare_property(name).
        commutative_only: If True, the function is used only where head.is_commutative.
        per_argument: If True, the function is called as fn(arg, copies) and returns how
            many copies of arg to keep. copies counts the arguments equal to arg that are
            next to each other, which is all of them where head.is_commutative.
        merges: If True, the function returns a list of (group, merged) pairs, and each
            merged replaces the arguments in its group. It is used only where
            head.is_commutative.

    Returns:
        A decorator. Unless per_argument is True, the function it registers is called as
        fn(head, args) and returns the new args, or an expression equal to head(*args).
        Either way getattr(head, name) is passed as one more argument, unless name starts
        with is_.

    >>> from nary import Many, NumberKind, declare_function, log
    >>> from nary.logic import true
    >>> from nary.normalising import normalise
    >>> from nary.properties import declare_properties, declare_property
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> declare_property("is_cancelled_by_a_copy")
    >>> @step("is_cancelled_by_a_copy", per_argument=True)
    ... def keep_one_of_an_odd_number(arg, copies):
    ...     return copies % 2
    >>> Toggle = declare_function("Toggle", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(
    ...     Toggle, is_associative=True, is_commutative=True, is_cancelled_by_a_copy=True,
    ... )
    >>> normalise(Toggle(x, y, x)), normalise(Toggle(x, y, x, x))
    (y, Toggle(x, y))
    >>> Queue = declare_function("Queue", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(Queue, is_associative=True, is_cancelled_by_a_copy=True)
    >>> normalise(Queue(x, x, y)), normalise(Queue(x, y, x))
    (y, Queue(x, y, x))

    A function that needs all the arguments at once, and the value of its property:

    >>> declare_property("inverse_function")
    >>> @step("inverse_function", commutative_only=True)
    ... def cancel(head, args, inverse):
    ...     for arg in args:
    ...         if inverse(arg) in args:
    ...             return [other for other in args if other not in (arg, inverse(arg))]
    ...     return args
    >>> undo = declare_function("undo", NumberKind, returns=NumberKind, domain=true)
    >>> Tally = declare_function("Tally", Many(NumberKind), returns=NumberKind, domain=true)
    >>> declare_properties(Tally, is_associative=True, is_commutative=True, inverse_function=undo)
    >>> normalise(Tally(x, y, undo(x)))
    y

    What a function returns is not used if it leaves out an argument that may have no value.

    >>> normalise(Tally(log(x), y, undo(log(x))))
    Tally(log(x), undo(log(x)), y)
    """
    if not is_property(name):
        raise ValueError(f"{name} is not a property")
    if name in _step_of_property:
        raise ValueError(f"{name} already has a step")

    def register(function: Callable) -> Callable:
        _step_of_property[name] = _Step(function, commutative_only or merges, per_argument, merges)
        return function

    return register


def apply_property_steps(
    head: Expr, args: list[Expr], has_a_value: Callable, normalise: Callable,
) -> Expr:
    """Build head(*args), with args changed by the functions that step registered.

    Args:
        head: A function.
        args: Its arguments, each already normalised.
        has_a_value: Called as has_a_value(arg, new_args). An argument is removed only
            where this returns True, new_args being what replaces it.
        normalise: Called as normalise(arg) on each argument that a function builds.

    Returns:
        head applied to the arguments that are left. If one is left, that argument.
        If none is left and head.identity_element is not None, head.identity_element.
        If a function returned an expression in place of the arguments, that expression.

    >>> from nary import Add, Mul, NumberKind, log, sin
    >>> from nary.normalising import normalise
    >>> from nary.rewriting import _has_a_value
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> has_a_value = lambda e, new_args: _has_a_value(e, lambda condition: False)
    >>> apply_property_steps(Mul, [y, Mul(x, 2), NumberKind(1)], has_a_value, normalise)
    Mul(2, x, y)
    >>> zero = NumberKind(0)
    >>> apply_property_steps(Mul, [sin(x), zero], has_a_value, normalise)
    0
    >>> apply_property_steps(Mul, [log(x), zero], has_a_value, normalise)
    Mul(0, log(x))
    >>> apply_property_steps(Add, [], has_a_value, normalise)
    0
    """
    commutative = head.is_commutative
    if head.is_associative or len(args) <= 2:
        new_args = _apply_steps_until_unchanged(head, args, commutative, has_a_value, normalise)
        if isinstance(new_args, Expr):
            return new_args
        if len(new_args) == 1 and (head.is_associative or len(args) > 1):
            return new_args[0]
        if not new_args and head.identity_element is not None:
            return head.identity_element
        args = new_args
    if commutative:
        args = sorted(args, key=_sort_key)
    return head(*args)


def _flattened(head: Expr, args: list[Expr]) -> list[Expr]:
    if not head.is_associative:
        return args
    flattened = []
    for arg in args:
        flattened += arg.args if not arg.is_atom and arg.head == head else [arg]
    return flattened


def _apply_steps_until_unchanged(
    head: Expr, args: list[Expr], commutative: bool, has_a_value: Callable, normalise: Callable,
) -> list[Expr] | Expr:
    properties = head.properties
    seen_before = set()
    while True:
        args = _flattened(head, args)
        if commutative:
            args = sorted(args, key=_sort_key)
        if tuple(args) in seen_before:
            raise RuntimeError(f"the steps for {head!r} never stop changing {args!r}")
        seen_before.add(tuple(args))
        args_after_steps = args
        for name, value in properties.items():
            registered = _step_of_property.get(name)
            if registered is None or (registered.commutative_only and not commutative):
                continue
            declared_value = () if name.startswith("is_") else (value,)
            args_after_steps = _apply_step_keeping_arguments_without_a_value(
                registered, head, args_after_steps, declared_value, has_a_value, normalise,
            )
            if isinstance(args_after_steps, Expr):
                return args_after_steps
        if args_after_steps == args:
            return args
        args = args_after_steps


def _apply_step_keeping_arguments_without_a_value(
    registered: _Step, head: Expr, args: list[Expr], declared_value: tuple,
    has_a_value: Callable, normalise: Callable,
) -> list[Expr] | Expr:
    if registered.per_argument:
        new_args = []
        for arg, equal_args in groupby(args):
            copies = len(list(equal_args))
            copies_to_keep = registered.function(arg, copies, *declared_value)
            if copies_to_keep == 0 and not has_a_value(arg, []):
                copies_to_keep = copies
            new_args += [arg] * copies_to_keep
        return new_args
    if registered.merges:
        new_args = list(args)
        for group, merged in registered.function(head, args, *declared_value):
            if all(has_a_value(arg, [merged]) for arg in group):
                for arg in group:
                    new_args.remove(arg)
                new_args.append(normalise(merged))
        return new_args
    result = registered.function(head, args, *declared_value)
    new_args = [result] if isinstance(result, Expr) else result
    if not all(has_a_value(arg, new_args) for arg in set(args) - set(new_args)):
        return args
    new_args = [arg if arg in args else normalise(arg) for arg in new_args]
    return new_args[0] if isinstance(result, Expr) else new_args


@step("identity_element", per_argument=True)
def _no_copies_of_the_identity(arg: Expr, copies: int, identity: Expr) -> int:
    return 0 if arg == identity else copies


@step("is_idempotent", per_argument=True)
def _one_copy_of_each(arg: Expr, copies: int) -> int:
    return min(copies, 1)


@step("absorbing_element")
def _only_the_absorbing_element(head: Expr, args: list[Expr], absorbing: Expr) -> list[Expr]:
    return [absorbing] if absorbing in args else args


@step("evaluate_literals")
def _literals_evaluated(
    head: Expr, args: list[Expr], evaluate_literals: Callable,
) -> list[Expr] | Expr:
    if not head.is_associative:
        if not all(arg.is_literal for arg in args):
            return args
        literal = _evaluated(head, args, evaluate_literals)
        return args if literal is None else literal
    ordered = sorted(args, key=lambda arg: not arg.is_literal) if head.is_commutative else args
    new_args = []
    for is_literal, run in groupby(ordered, key=lambda arg: arg.is_literal):
        run = list(run)
        literal = _evaluated(head, run, evaluate_literals) if is_literal and len(run) > 1 else None
        new_args += run if literal is None else [literal]
    return new_args if len(new_args) < len(args) else args


def _evaluated(head: Expr, literals: list[Expr], evaluate_literals: Callable) -> Expr | None:
    value = evaluate_literals(*(literal.value for literal in literals))
    return None if value is None else head.kind.output(value)
