"""Applying rewrite rules: ``rewrite(e, rules, known=None)``.

This is the engine that applies rules written with ``nary.rules``. It
uses each rule's ``pattern``, ``replacement``, ``condition``, ``erased`` and
``literal_variables``, the facts ``unordered`` and ``flat``, and what
``computes`` records. It returns a new expression; the expression given is
never changed, because expressions are immutable.

    >>> from nary import NumberKind, log, sin
    >>> from nary.arithmetic_rules import rules
    >>> from nary.rewriting import rewrite
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> rewrite((x + 0) * 1 + y * 0, rules)
    x
    >>> rewrite(sin(x) * 0, rules)
    0
    >>> rewrite(log(x) * 0, rules)               # log(0) * 0 has no value
    Mul(log(x), 0)
    >>> rewrite(x / x, rules), rewrite(x / x, rules, known=lambda c: True)
    (Mul(x, Pow(x, -1)), 1)

``rules`` is any iterable of ``Rule``. ``known`` is a Python function that is
given a ``BoolKind`` expression and returns ``True`` if that condition is
known to hold; any other answer means not known. Without ``known`` nothing is
known. ``known`` is the only place where assumptions enter: this module
decides nothing about conditions itself, except that the constant ``true``
holds.

How it works, in seven points:

1. Order of work. The head and the arguments of an application are
   rewritten first, then the application itself. When a rule applies, the
   result is rewritten again, until no rule applies. Rules are tried in the
   order given, and the first that applies is used. Making the rules
   terminate is up to whoever writes them, with one guard: a rule whose
   result equals the expression it was applied to counts as not applying.
2. Flattening. If the head is a declared function recorded as ``flat``,
   arguments that are applications of the same function are merged into it
   before matching: ``Add(Add(x, y), z)`` is matched as ``Add(x, y, z)``. If
   no rule applies, the expression is returned as it was, not flattened.
3. Matching. A symbol in a pattern is a variable: it matches any expression
   of the same kind, and a variable that appears twice must match equal
   expressions. This includes a symbol of a function kind in the head of a
   pattern, such as ``f`` in ``f(a)``. A literal or a constant matches only
   itself. An application matches an application whose head matches and
   whose arguments match. Arguments match by position, with the same number
   of arguments, unless the head of the pattern is recorded as
   ``unordered``: then each argument of the pattern must match a different
   argument of the expression, in any order (tried deterministically:
   pattern arguments left to right, each against the expression arguments
   left to right). A variable always matches exactly one argument, never
   several. Only at the top of a pattern, and only when its head is both
   ``unordered`` and ``flat``, the pattern may match some of the arguments
   of a longer application; the others are kept. The replacement takes the
   place of the first matched argument, the other arguments keep their
   order, and the result is flattened again: ``a + 0 -> a`` turns
   ``Add(x, 0, y)`` into ``Add(x, y)``, and ``a + a -> 2 * a`` turns
   ``Add(x, y, x)`` into ``Add(Mul(2, x), y)``. A function recorded as
   ``flat`` but not ``unordered`` is matched by position (there is none yet).
   A literal variable of the rule (one inside ``computed(...)``) matches
   only a literal; a way of matching that binds it to anything else is
   skipped.
4. Conditions. A condition holds when it is the constant ``true`` or
   ``known`` returns ``True`` for it. Nothing else is evaluated or
   simplified: ``Or(Ne(2, 0), ...)`` is given to ``known`` as it is. A rule
   with a condition applies only if the condition holds, with each variable
   replaced by what it matched.
5. Erased variables. A rule that erases a variable (``a`` in ``a * 0 -> 0``)
   is sound only where what the variable matched has a value. This engine
   accepts that when it can show it from the declared domains
   (``nary.domains``): a symbol, a literal or a constant has a value, and an
   application ``f(args)`` of a declared function has one when ``f`` has a
   stated domain, every argument has a value, and the domain of ``f``
   applied to the arguments holds. So ``x * 0`` and ``sin(x) * 0`` become
   ``0``, but ``log(x) * 0`` is left alone unless ``Ne(x, 0)`` is known.
   An application of a function declared with ``domain=None``, a lambda, a
   call of a lambda, and an application of an unknown function, such as
   ``f(x)``, are not known to have a value. The check applies to every rule that erases a variable,
   with or without a condition. If one way of matching fails a condition or
   this check, the next way is tried.
6. Computed literals. In the replacement, after each variable is replaced
   by what it matched, each ``computed(e)`` is replaced by the literal of
   the integer value of ``e``, worked out with the Python functions
   recorded with ``computes``: with ``rule(m + n, computed(m + n))``,
   ``Add(2, 3)`` becomes ``5``. This is the only arithmetic the engine does,
   and only where a rule asks for it.
7. Lambdas. A lambda is returned unchanged: the engine does not look inside
   it, because its variables are not the free symbols that ``known`` talks
   about. The arguments of a call of a lambda are still rewritten.

Deliberately not here: putting arguments in a canonical order, strategies
or options, assumptions, and a pattern written with a flat function nested
in itself (``a + b + a``) is not flattened, so at the top it never matches.

The module is imported as ``nary.rewriting``; its names are not re-exported
from ``nary``.
"""

from ._core import Expr
from .domains import domain
from .functions import is_lambda
from .logic import true
from .rules import computation, computed, is_flat, is_unordered

__all__ = ["rewrite"]


def rewrite(e, rules, known=None):
    """``e`` rewritten with ``rules`` until no rule applies.

    ``known(condition)`` returning ``True`` means the ``BoolKind``
    expression ``condition`` is known to hold.
    """
    if not isinstance(e, Expr):
        raise TypeError(f"rewrite expects an expression, got {e!r}")
    return _rewrite(e, tuple(rules), known or (lambda condition: False))


def _rewrite(e, rules, known):
    if e.head is None or is_lambda(e):
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
    """The result of applying ``rule`` at the top of ``e``, or ``None``."""
    for bindings, used in _match_top(rule.pattern, e):
        if not all(bindings[v].is_literal for v in rule.literal_variables):
            continue
        condition = rule.condition
        if condition is not None and not _holds(_substitute(condition, bindings), known):
            continue
        if not all(_has_a_value(bindings[v], known) for v in rule.erased):
            continue
        replacement = _substitute(rule.replacement, bindings)
        if used is None:
            return replacement
        # Some arguments were not matched: the replacement takes the place
        # of the first matched one, and the rest are kept in order.
        first = min(used)
        args = [replacement if i == first else arg
                for i, arg in enumerate(e.args) if i == first or i not in used]
        return _flatten(e.head(*args))
    return None


def _holds(condition, known):
    """Whether ``condition`` holds. See point 4 of the docstring."""
    return condition == true or known(condition) is True


def _has_a_value(e, known):
    """Whether ``e`` certainly has a value. See point 5 of the docstring."""
    if e.is_symbol or e.is_literal or e.is_constant:
        return True
    # The head of a lambda is declared with domain=None, so a lambda has no
    # domain here, and neither has a call of a lambda or of an unknown function.
    condition = domain(e.head) if _is_declared(e.head) else None
    if condition is None:
        return False
    return (all(_has_a_value(arg, known) for arg in e.args)
            and _holds(condition(*e.args), known))


def _flatten(e):
    """``e`` with arguments that are applications of the same flat function
    merged into it, one level, as in ``Add(Add(x, y), z) -> Add(x, y, z)``."""
    if not (_is_declared(e.head) and is_flat(e.head)):
        return e
    if not any(arg.head == e.head for arg in e.args):
        return e
    args = []
    for arg in e.args:
        args.extend(arg.args if arg.head == e.head else (arg,))
    return e.head(*args)


def _is_declared(head):
    """Whether ``head`` is a declared function. A head is of a function
    kind, so it is a declared function exactly when it is a constant."""
    return head is not None and head.is_constant


def _match_top(pattern, e):
    """Every way the top of a rule's pattern matches ``e``, as pairs
    ``(bindings, used)``. ``used`` is ``None`` when the whole of ``e`` is
    matched, and otherwise the positions of the arguments of ``e`` that
    were matched, when the head is unordered and flat (point 3)."""
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
        elif used:  # a pattern with no arguments matches only itself
            yield bindings, set(used)


def _match(pattern, e, bindings):
    """Every way ``pattern`` matches all of ``e``, given ``bindings`` from
    variables to expressions. A dictionary is never changed in place."""
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
    elif e.head is not None:
        for with_head in _match(pattern.head, e.head, bindings):
            if _is_declared(pattern.head) and is_unordered(pattern.head):
                for new, used in _match_unordered(pattern.args, e.args, with_head, ()):
                    if len(used) == len(e.args):
                        yield new
            elif len(pattern.args) == len(e.args):
                yield from _match_in_order(pattern.args, e.args, with_head)


def _match_in_order(patterns, args, bindings):
    """Every way each pattern matches the argument at the same position."""
    if not patterns:
        yield bindings
        return
    for new in _match(patterns[0], args[0], bindings):
        yield from _match_in_order(patterns[1:], args[1:], new)


def _match_unordered(patterns, args, bindings, used):
    """Every way each pattern matches a different one of ``args``, as pairs
    ``(bindings, used)`` with ``used`` the positions matched, in the order
    of the patterns. Some of ``args`` may be left over."""
    if not patterns:
        yield bindings, used
        return
    for i, arg in enumerate(args):
        if i not in used:
            for new in _match(patterns[0], arg, bindings):
                yield from _match_unordered(patterns[1:], args, new, used + (i,))


def _substitute(e, bindings):
    """``e`` with each variable in ``bindings`` replaced by what it matched,
    and each ``computed(...)`` by its literal (point 6). ``e`` is the
    replacement or the condition of a rule, so it contains no lambda."""
    if e.is_symbol:
        return bindings.get(e, e)
    if e.head is None:
        return e
    if e.head == computed:
        return e.kind(_integer(_substitute(e.args[0], bindings)))
    return _substitute(e.head, bindings)(*(_substitute(arg, bindings) for arg in e.args))


def _integer(e):
    """The integer value of ``e``, made of literals and functions recorded
    with ``computes``, as ``nary.rules`` checks."""
    if e.is_literal:
        return e.value
    return computation(e.head)(*(_integer(arg) for arg in e.args))
