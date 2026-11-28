from __future__ import annotations

from collections.abc import Callable, Iterator
from itertools import groupby
from typing import NamedTuple

from ._core import Expr
from .properties import heads_declaring, is_property

__all__ = ["apply_property_steps", "step"]


class _Step(NamedTuple):
    function: Callable
    commutative_only: bool
    per_argument: bool
    merges: bool
    on_the_value: bool


_step_of_property: dict[str, _Step] = {}


def step(
    name: str, commutative_only: bool = False, per_argument: bool = False, merges: bool = False,
    on_the_value: bool = False,
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
        on_the_value: If True, the function is used on each head that is getattr(F, name)
            for some function F, and F is passed in place of the value.

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
        commutative = commutative_only or merges
        _step_of_property[name] = _Step(function, commutative, per_argument, merges, on_the_value)
        return function

    return register


def apply_property_steps(head: Expr, args: list[Expr], has_a_value: Callable) -> Expr:
    """Build head(*args), with args changed by the first function that step registered to change them.

    Args:
        head: A function.
        args: Its arguments, each already normalised, in order of repr where head.is_commutative.
        has_a_value: Called as has_a_value(arg, new_args). An argument is removed only
            where this returns True, new_args being what replaces it.

    Returns:
        head applied to the arguments that are left. If one is left, that argument.
        If none is left and head.identity_element is not None, head.identity_element.
        If a function returned an expression in place of the arguments, that expression.
        What a function builds is not normalised.

    >>> from nary import Add, Mul, NumberKind, log, sin
    >>> from nary.rewriting import _has_a_value
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> has_a_value = lambda e, new_args: _has_a_value(e, lambda condition: False)
    >>> apply_property_steps(Mul, [NumberKind(1), Mul(x, 2), y], has_a_value)
    Mul(1, x, 2, y)
    >>> apply_property_steps(Mul, [NumberKind(1), NumberKind(2), x], has_a_value)
    Mul(2, x)
    >>> zero = NumberKind(0)
    >>> apply_property_steps(Mul, [zero, sin(x)], has_a_value)
    0
    >>> apply_property_steps(Mul, [zero, log(x)], has_a_value)
    Mul(0, log(x))
    >>> apply_property_steps(Add, [], has_a_value)
    0
    """
    new_args = _flattened(head, args)
    if new_args == args and (head.is_associative or len(args) <= 2):
        new_args = _apply_first_changing_step(head, args, has_a_value)
        if isinstance(new_args, Expr):
            return new_args
    if len(new_args) == 1 and (head.is_associative or len(args) > 1):
        return new_args[0]
    if not new_args and head.identity_element is not None:
        return head.identity_element
    return head(*new_args)


def _flattened(head: Expr, args: list[Expr]) -> list[Expr]:
    if not head.is_associative:
        return args
    flattened = []
    for arg in args:
        flattened += arg.args if not arg.is_atom and arg.head == head else [arg]
    return flattened


def _apply_first_changing_step(
    head: Expr, args: list[Expr], has_a_value: Callable,
) -> list[Expr] | Expr:
    for registered, declared_value in _steps_and_values(head):
        if registered.commutative_only and not head.is_commutative:
            continue
        new_args = _apply_step_keeping_arguments_without_a_value(
            registered, head, args, declared_value, has_a_value,
        )
        if isinstance(new_args, Expr) or new_args != args:
            return new_args
    return args


def _steps_and_values(head: Expr) -> Iterator[tuple[_Step, tuple]]:
    for name, value in head.properties.items():
        registered = _step_of_property.get(name)
        if registered is not None and not registered.on_the_value:
            yield registered, () if name.startswith("is_") else (value,)
    for name, registered in _step_of_property.items():
        if registered.on_the_value:
            for declaring in heads_declaring(name, head):
                yield registered, (declaring,)


def _apply_step_keeping_arguments_without_a_value(
    registered: _Step, head: Expr, args: list[Expr], declared_value: tuple, has_a_value: Callable,
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
                new_args.append(merged)
        return new_args
    result = registered.function(head, args, *declared_value)
    new_args = [result] if isinstance(result, Expr) else result
    return result if all(has_a_value(arg, new_args) for arg in set(args) - set(new_args)) else args


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
        value = evaluate_literals(*(arg.value for arg in args))
        return args if value is None else value
    ordered = sorted(args, key=lambda arg: not arg.is_literal) if head.is_commutative else args
    new_args = []
    for literal, run in groupby(ordered, key=lambda arg: arg.is_literal):
        run = list(run)
        value = evaluate_literals(*(arg.value for arg in run)) if literal and len(run) > 1 else None
        new_args += run if value is None else [value]
    return new_args if len(new_args) < len(args) else args


@step("distributes_over", merges=True, on_the_value=True)
def _terms_that_differ_by_a_coefficient_added(
    head: Expr, args: list[Expr], product: Expr,
) -> list[tuple[list[Expr], Expr]]:
    terms_and_coefficients = {}
    for arg in args:
        split = _coefficient_and_the_rest(arg, product, head)
        if split is not None:
            coefficient, rest = split
            terms_and_coefficients.setdefault(rest, []).append((arg, coefficient))
    return [
        ([term for term, _ in group], product(*before, head(*(c for _, c in group)), *after))
        for (before, after), group in terms_and_coefficients.items() if len(group) > 1
    ]


def _coefficient_and_the_rest(
    term: Expr, product: Expr, total: Expr,
) -> tuple[Expr, tuple[tuple[Expr, ...], tuple[Expr, ...]]] | None:
    """(c, (before, after)) with term equal to product(*before, c, *after), or None.

    >>> from nary import Add, Mul, NumberKind
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> _coefficient_and_the_rest(Mul(3, x, y), Mul, Add)
    (3, ((), (x, y)))
    >>> _coefficient_and_the_rest(Mul(x, y), Mul, Add), _coefficient_and_the_rest(x, Mul, Add)
    ((1, ((), (x, y))), (1, ((), (x,))))
    """
    if term.is_literal:
        return None
    kind = total.kind.output
    args = term.args if not term.is_atom and term.head == product else None
    literals = [i for i, arg in enumerate(args or ()) if arg.is_literal and arg.kind == kind]
    if len(literals) == 1:
        i = literals[0]
        if product.is_commutative:
            return args[i], ((), args[:i] + args[i + 1:])
        return args[i], (args[:i], args[i + 1:])
    identity = product.identity_element
    if identity is None or identity.kind != kind:
        return None
    return identity, ((), args if args is not None and product.is_associative else (term,))
