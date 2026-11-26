"""Conditions are proved by satassume, after translating them to Q facts.

    >>> import nary as nr
    >>> x = nr.NumberKind("x")
    >>> known = prover(nr.Gt(x, 1))
    >>> known(nr.Ne(x, 0)), known(nr.Lt(x, 0)), known(nr.Eq(nr.re(x), x))
    (True, False, True)

definedness is where an expression has a value: the domains of its parts.

    >>> definedness(nr.log(x) / x)
    And(Ne(x, 0), Or(Ne(x, 0), Gt(re(-1), 0)))
    >>> definedness(nr.sin(x) + 1)
    true
"""

import sympy
from satassume.sympy_api import ask

from nary.domains import domain_of
from nary.logic import And, Not, Or, true

from .translate import Untranslatable, to_sympy

__all__ = ["definedness", "implies", "prover"]


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


def implies(a, b):
    return b if a == true else Or(Not(a), b)


def prover(assumptions=true, log=None):
    facts = to_sympy(assumptions)
    answers = {}

    def known(condition):
        if condition == true:
            return True
        if condition not in answers:
            answers[condition] = _proved(condition, facts)
            if answers[condition] and log is not None:
                log.append(condition)
        return answers[condition]

    return known


def _proved(condition, facts):
    try:
        question = to_sympy(condition)
    except Untranslatable:
        return False
    if question in (sympy.true, sympy.false):
        return question is sympy.true
    try:
        return ask(question, facts) is True
    except (ValueError, TypeError):
        return False
