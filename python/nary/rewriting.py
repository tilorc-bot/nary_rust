"""rewrite applies the rules until none applies.

    >>> from nary import Add, Gt, Many, Ne, NumberKind, log, pi, sin
    >>> from nary.arithmetic_rules import rules
    >>> from nary.rewriting import beta, has_a_value, holds, rewrite
    >>> from nary.rules import rule
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

    >>> rewrite(x / x, rules), rewrite(x / x, rules, known=lambda c: c == Ne(x, 0))
    (Mul(x, Pow(x, -1)), 1)

A run variable matches the arguments that are left, at any depth.

    >>> a, rest = NumberKind("a"), Many(NumberKind)("rest")
    >>> period = rule(sin(Add(a, 2 * pi, rest)), sin(Add(a, rest)))
    >>> rewrite(sin(Add(y, 2 * pi, x)) + 1, [period])
    Add(sin(Add(y, x)), 1)

A normal form is applied at each node before the rules.

    >>> rewrite(sin(x + 0), rules, normal=lambda e, known: x if e == x + 0 else e)
    sin(x)

holds also follows implications from known facts.

    >>> holds(Ne(x, 0), lambda c: c == Gt(x, 0)), has_a_value(log(x), None)
    (True, False)

beta puts the argument of a lambda in place of its variable.

    >>> from nary import Lambda
    >>> beta(Lambda(y, y + 1)(x))
    Add(x, 1)
"""

from ._core import Expr
from .domains import domain_of
from .functions import is_lambda
from .kinds import NumberKind
from .logic import And, Or, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re
from ._identities import Law, identities
from .rules import is_flat, is_run, is_unordered

__all__ = ["beta", "has_a_value", "holds", "implications", "rewrite"]

a, b = NumberKind("a"), NumberKind("b")

implications = [
    (Gt(a, b), Ne(a, b)),
    (Lt(a, b), Ne(a, b)),
    (Gt(b, a), Ne(a, b)),
    (Lt(b, a), Ne(a, b)),
    (Ne(b, a), Ne(a, b)),
    (Gt(a, 0), Ge(a, 0)),
    (Lt(a, 0), Le(a, 0)),
    (Gt(a, 0), Eq(re(a), a)),
    (Lt(a, 0), Eq(re(a), a)),
    (Ge(a, 0), Eq(re(a), a)),
    (Le(a, 0), Eq(re(a), a)),
    (Gt(re(a), 0), Ne(a, 0)),
    (Lt(re(a), 0), Ne(a, 0)),
]


def rewrite(e, rules, known=None, normal=None):
    if not isinstance(e, Expr):
        raise TypeError(f"rewrite expects an expression, got {e!r}")
    return _Rewriting(tuple(rules), known, normal, 1).rewrite(e)


def holds(c, known=None, depth=2):
    if c == true or (known is not None and known(c) is True):
        return True
    if c.head == And:
        return all(holds(arg, known, depth) for arg in c.args)
    if c.head == Or:
        return any(holds(arg, known, depth) for arg in c.args)
    return depth > 0 and any(
        holds(_substitute(premise, bindings), known, depth - 1)
        for premise, conclusion in implications for bindings in _match(conclusion, c, {})
    )


def has_a_value(e, known=None):
    if e.is_symbol or e.is_literal or e.is_constant:
        return True
    if not _is_declared(e.head):
        return False
    condition = domain_of(e)
    if condition is None:
        return False
    return all(has_a_value(arg, known) for arg in e.args) and holds(condition, known)


def beta(e):
    if e.head is None or not is_lambda(e.head):
        return e
    *variables, body = e.head.args
    stack = [body]
    while stack:
        sub = stack.pop()
        if is_lambda(sub):
            return e
        if sub.head is not None:
            stack.extend((sub.head, *sub.args))
    return _substitute(body, dict(zip(variables, e.args)))


class _Rewriting:
    def __init__(self, rules, known, normal, depth):
        self.rules, self.known, self.normal, self.done = rules, known, normal, {}
        self.inner = _Rewriting(rules, known, normal, depth - 1) if depth else None

    def ask(self, c):
        if self.known is not None and self.known(c) is True:
            return True
        return self.inner is not None and self.inner.rewrite(c) == true

    def rewrite(self, e):
        if e not in self.done:
            self.done[e] = e
            self.done[e] = self._rewrite(e)
        return self.done[e]

    def _rewrite(self, e):
        if e.head is None or is_lambda(e):
            return e
        head = self.rewrite(e.head)
        args = tuple(map(self.rewrite, e.args))
        if head != e.head or args != e.args:
            e = _flatten(head(*args))
        if self.normal is not None:
            result = self.normal(e, self.ask)
            if result != e:
                return self.rewrite(result)
        flat_e = _flatten(e)
        for rule in self.rules:
            result = _apply(rule, flat_e, self.ask)
            if result is not None and result != flat_e:
                return self.rewrite(result)
        return e


def _apply(rule, e, known):
    for bindings, used in _match_top(rule.pattern, e):
        condition = rule.condition
        if condition is not None and not holds(_substitute(condition, bindings), known):
            continue
        erased = (bindings[v] if is_run(v) else (bindings[v],) for v in rule.erased)
        if not all(has_a_value(arg, known) for args in erased for arg in args):
            continue
        replacement = _substitute(rule.replacement, bindings)
        if used is None:
            return replacement
        first = min(used)
        args = [replacement if i == first else arg
                for i, arg in enumerate(e.args) if i == first or i not in used]
        return _flatten(e.head(*args))
    return None


def _flatten(e):
    if not (_is_declared(e.head) and is_flat(e.head)):
        return e
    args = []
    for arg in e.args:
        args.extend(arg.args if arg.head == e.head else (arg,))
    unit = _unit(e.head)
    if unit is not None and len(args) < 2:
        return args[0] if args else unit
    return e.head(*args) if len(args) != len(e.args) or args != list(e.args) else e


def _is_declared(head):
    return head is not None and head.is_constant


def _match_top(pattern, e):
    head = pattern.head
    if any(map(is_run, pattern.args)) or e.head != head or len(e.args) < len(pattern.args) or not (
        is_unordered(head) and is_flat(head)
    ):
        for bindings in _match(pattern, e, {}):
            yield bindings, None
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
    elif pattern.head is None:
        if pattern == e:
            yield bindings
    elif e.head != pattern.head and _unit(pattern.head) is not None:
        yield from _match_args(pattern, (e,), bindings)
    elif e.head is not None:
        for with_head in _match(pattern.head, e.head, bindings):
            yield from _match_args(pattern, e.args, with_head)


def _unit(head):
    if not (_is_declared(head) and is_flat(head)):
        return None
    units = [law.args[0] for law in identities(head) if isinstance(law, Law) and law.title == "identity"]
    if not units:
        return None
    return units[0] if isinstance(units[0], Expr) else head.kind.output(units[0])


def _match_args(pattern, args, bindings):
    runs = [p for p in pattern.args if is_run(p)]
    fixed = [p for p in pattern.args if not is_run(p)]
    unit = _unit(pattern.head)
    if unit is not None and len(args) < len(fixed):
        args = args + (unit,) * (len(fixed) - len(args))
    if _is_declared(pattern.head) and is_unordered(pattern.head):
        for new, used in _match_unordered(fixed, args, bindings, ()):
            yield from _bind_run(runs, tuple(a for i, a in enumerate(args) if i not in used), new)
    elif len(fixed) <= len(args) and (runs or len(fixed) == len(args)):
        start = pattern.args.index(runs[0]) if runs else len(args)
        end = start + len(args) - len(fixed)
        for new in _match_in_order(fixed, args[:start] + args[end:], bindings):
            yield from _bind_run(runs, args[start:end], new)


def _bind_run(runs, rest, bindings):
    if not runs:
        if not rest:
            yield bindings
    elif bindings.get(runs[0], rest) == rest:
        yield {**bindings, runs[0]: rest}


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
    if e.head is None:
        return e
    args = []
    for arg in e.args:
        args.extend(bindings.get(arg, (arg,)) if is_run(arg) else (_substitute(arg, bindings),))
    return _flatten(_substitute(e.head, bindings)(*args))
