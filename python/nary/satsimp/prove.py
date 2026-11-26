"""Conditions are proved from the assumptions by decide: nary's properties and autosimp, given the conjuncts as known.

    >>> import nary as nr
    >>> x = nr.NumberKind("x")
    >>> known = prover(nr.Gt(x, 0))
    >>> known(nr.Ne(x, 0)), known(nr.Lt(x, 0)), known(nr.Eq(nr.re(x), x))
    (True, False, True)

A known value is substituted, and an implication is proved by assuming its antecedent.

    >>> prover(nr.Eq(x, 0))(nr.Eq(nr.I * nr.pi * x, 0))
    True
    >>> c = nr.Ne(nr.cos(x), 0)
    >>> known(implies(c, nr.Ne(nr.cos(x) * x, 0))), known(implies(c, nr.Ne(nr.cos(x) * (x - 1), 0)))
    (True, False)

definedness is where an expression has a value: the domains of its parts.

    >>> definedness(nr.log(x) / x)
    And(Ne(x, 0), Or(Ne(x, 0), Gt(re(-1), 0)))
    >>> definedness(nr.sin(x) + 1)
    true

relied is the part of the input's domain that the result's domain and the assumptions do not give back.

    >>> relied(nr.cos(x) * nr.tan(x), nr.sin(x)), relied(nr.log(x) / x, nr.log(x))
    (Ne(cos(x), 0), true)
"""

from functools import cache

from nary.autosimp import autosimp
from nary import Eq
from nary.domains import domain_of
from nary.logic import And, Not, Or, true
from nary.properties import holds
from nary.rewriting import _substitute

__all__ = ["conjuncts", "decide", "definedness", "implies", "prover", "relied"]


def _parts(e):
    stack = [e]
    while stack:
        e = stack.pop()
        if e.head is not None:
            yield e
            stack.extend(reversed(e.args))


def definedness(e):
    conditions = {}
    for part in _parts(e):
        if not (part.head.is_constant and part.head.kind.inputs is not None):
            return None
        condition = domain_of(part)
        if condition is None:
            return None
        if condition != true:
            conditions[condition] = None
    return And(*conditions) if conditions else true


def _all(conditions):
    conditions = sorted(conditions - {true}, key=repr)
    return true if not conditions else conditions[0] if len(conditions) == 1 else And(*conditions)


def relied(e, result, assumptions=true):
    before, after = definedness(e), definedness(result)
    if after is None:
        return before
    known, given = prover(And(assumptions, after)), conjuncts(assumptions)
    return _all({autosimp(c, given) for c in conjuncts(before) - conjuncts(after) if not known(c)})


def implies(a, b):
    return b if a == true else Or(Not(a), b)


def conjuncts(condition):
    if condition == true:
        return frozenset()
    if condition.head == And:
        return frozenset().union(*map(conjuncts, condition.args))
    return frozenset([condition])


@cache
def _simplified(known):
    return conjuncts(autosimp(And(*known))) if known else known


def decide(condition, known):
    known = _simplified(known)
    condition = _substitute(condition, {c.args[0]: c.args[1] for c in known if c.head == Eq and c.args[0].is_symbol})
    if holds(condition, known) or autosimp(condition, known) == true:
        return True
    if condition.head == Or and any(c.head == Not for c in condition.args):
        assumed = known.union(*(conjuncts(autosimp(c.args[0], known)) for c in condition.args if c.head == Not))
        rest = [c for c in condition.args if c.head != Not]
        return bool(rest) and decide(Or(*rest) if len(rest) > 1 else rest[0], assumed)
    return False


def prover(assumptions=true, log=None, decide=decide):
    known, answers = conjuncts(assumptions), {}

    def proved(condition):
        if condition == true:
            return True
        if condition not in answers:
            answers[condition] = decide(condition, known)
            if answers[condition] and log is not None:
                log.append(condition)
        return answers[condition]

    return proved
