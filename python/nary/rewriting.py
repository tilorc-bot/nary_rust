"""rewrite applies the rules until none applies.

    >>> from nary import NumberKind, log, sin
    >>> from nary.arithmetic_rules import rules
    >>> from nary.rewriting import rewrite
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> rewrite((x + 0) * 1 + y * 0, rules)
    x

The rule a * 0 -> 0 applies when the erased part has a value.

    >>> rewrite(sin(x) * 0, rules)
    0

It does not apply when the erased part may have no value.

    >>> rewrite(log(x) * 0, rules)               # log(0) * 0 has no value
    Mul(log(x), 0)

A condition holds when known returns True for it.

    >>> rewrite(x / x, rules), rewrite(x / x, rules, known=lambda c: True)
    (Mul(x, Pow(x, -1)), 1)
"""

from ._core import Expr
from .domains import domain_of
from .functions import is_lambda
from .logic import true
from .rules import is_flat, is_unordered

__all__ = ["rewrite"]


def rewrite(e, rules, known=None):
    if not isinstance(e, Expr):
        raise TypeError(f"rewrite expects an expression, got {e!r}")
    return _rewrite(e, tuple(rules), known or (lambda condition: False))


def _rewrite(e, rules, known):
    if e.is_atom or is_lambda(e):
        return e
    head = _rewrite(e.head, rules, known)
    args = tuple(_rewrite(arg, rules, known) for arg in e.args)
    if head != e.head or args != e.args:
        e = head(*args)
    flat_e = _flatten(e)
    for rule in rules:
        result = _apply(rule, flat_e, known)
        if result is not None and result != flat_e:
            return _rewrite(result, rules, known)
    return e


def _apply(rule, e, known):
    for bindings, used in _match_top(rule.pattern, e):
        condition = rule.condition
        if condition is not None and not _holds(_substitute(condition, bindings), known):
            continue
        if not all(_has_a_value(bindings[v], known) for v in rule.erased):
            continue
        replacement = _substitute(rule.replacement, bindings)
        if used is None:
            return replacement
        first = min(used)
        args = [replacement if i == first else arg
                for i, arg in enumerate(e.args) if i == first or i not in used]
        return _flatten(e.head(*args))
    return None


def _holds(condition, known):
    return condition == true or known(condition) is True


def _has_a_value(e, known):
    """Whether e is known to have a value, given the conditions that known says hold.

    >>> from nary import Lambda, Ne, NumberKind, log, pi, sin
    >>> from nary.calculus import Integral
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> nothing = lambda condition: False
    >>> _has_a_value(x, nothing), _has_a_value(NumberKind(2), nothing), _has_a_value(pi, nothing)
    (True, True, True)

    An application has a value when its arguments do and its domain holds.

    >>> _has_a_value(sin(x), nothing), _has_a_value(log(x), nothing), _has_a_value(sin(log(x)), nothing)
    (True, False, False)
    >>> _has_a_value(log(x), lambda condition: condition == Ne(x, 0))
    True

    It is not known to have one when its head is not declared or has no domain.

    >>> _has_a_value(Lambda(y, y)(x), nothing), _has_a_value(Integral(sin, 0, x), nothing)
    (False, False)

    A lambda has a value when its body does.

    >>> _has_a_value(Lambda(y, sin(y)), nothing), _has_a_value(Lambda(y, log(y)), nothing)
    (True, False)
    """
    if e.is_symbol or e.is_literal or e.is_constant:
        return True
    if not _is_declared(e.head):
        return False
    condition = domain_of(e)
    if condition is None:
        return False
    return all(_has_a_value(arg, known) for arg in e.args) and _holds(condition, known)


def _flatten(e):
    if not (_is_declared(e.head) and is_flat(e.head)):
        return e
    if not any(arg.head == e.head for arg in e.args):
        return e
    args = []
    for arg in e.args:
        args.extend(arg.args if arg.head == e.head else (arg,))
    return e.head(*args)


def _is_declared(head):
    return head is not None and head.is_constant


def _match_top(pattern, e):
    head = pattern.head
    if not (_is_declared(head) and is_unordered(head) and is_flat(head)):
        for bindings in _match(pattern, e, {}):
            yield bindings, None
        return
    if e.head != head:
        return
    for bindings, used in _match_unordered(pattern.args, e.args, {}, ()):
        if len(used) == len(e.args):
            yield bindings, None
        elif used:
            yield bindings, set(used)


def _match(pattern, e, bindings):
    if pattern.is_symbol:
        if pattern.kind != e.kind:
            return
        if pattern not in bindings:
            yield {**bindings, pattern: e}
        elif bindings[pattern] == e:
            yield bindings
    elif pattern.is_atom:
        if pattern == e:
            yield bindings
    elif not e.is_atom:
        for with_head in _match(pattern.head, e.head, bindings):
            if _is_declared(pattern.head) and is_unordered(pattern.head):
                for new, used in _match_unordered(pattern.args, e.args, with_head, ()):
                    if len(used) == len(e.args):
                        yield new
            elif len(pattern.args) == len(e.args):
                yield from _match_in_order(pattern.args, e.args, with_head)


def _match_in_order(patterns, args, bindings):
    if not patterns:
        yield bindings
        return
    for new in _match(patterns[0], args[0], bindings):
        yield from _match_in_order(patterns[1:], args[1:], new)


def _match_unordered(patterns, args, bindings, used):
    if not patterns:
        yield bindings, used
        return
    for i, arg in enumerate(args):
        if i not in used:
            for new in _match(patterns[0], arg, bindings):
                yield from _match_unordered(patterns[1:], args, new, used + (i,))


def _substitute(e, bindings):
    if e.is_symbol:
        return bindings.get(e, e)
    if e.is_atom:
        return e
    return _substitute(e.head, bindings)(*(_substitute(arg, bindings) for arg in e.args))
