import itertools
import random
from fractions import Fraction

import sympy

import nary as nr
from nary import Add, E, I, Mul, Pow, cos, exp, log, pi, re, sin, tan
from nary.autosimp import autosimp, key
from nary.domains import domain, domain_of
from nary.logic import And, Not, Or, false, true
from nary.properties import number, rational
from numeric import counterexamples

FUNCTIONS = {
    Add: sympy.Add, Mul: sympy.Mul, Pow: sympy.Pow, sin: sympy.sin, cos: sympy.cos,
    tan: sympy.tan, exp: sympy.exp, log: sympy.log, re: sympy.re,
    nr.Eq: sympy.Eq, nr.Ne: sympy.Ne, nr.Lt: sympy.Lt, nr.Gt: sympy.Gt, nr.Le: sympy.Le,
    nr.Ge: sympy.Ge, And: sympy.And, Or: sympy.Or, Not: sympy.Not,
}
CONSTANTS = {pi: sympy.pi, E: sympy.E, I: sympy.I, true: sympy.true, false: sympy.false}
BACK = {v: k for k, v in FUNCTIONS.items()}
BACK_CONSTANTS = {v: k for k, v in CONSTANTS.items()}
SIGNS = {nr.Lt: "negative", nr.Le: "nonpositive", nr.Ge: "nonnegative"}
NO_VALUE = (sympy.zoo, sympy.nan, sympy.oo, -sympy.oo)


class Unrepresentable(Exception):
    pass


def sympy_assumptions(known):
    assumptions = {}
    for c in known:
        lhs, rhs = c.args
        if c.head == nr.Ne and lhs.is_symbol and rhs == nr.NumberKind(0):
            assumptions.setdefault(lhs.name, {})["zero"] = False
        elif c.head == nr.Gt and lhs.is_symbol and rhs == nr.NumberKind(0):
            assumptions.setdefault(lhs.name, {})["positive"] = True
        elif c.head == nr.Eq and rhs.is_symbol and lhs == re(rhs):
            assumptions.setdefault(rhs.name, {})["real"] = True
        elif c.head in SIGNS and lhs.is_symbol and rhs == nr.NumberKind(0):
            assumptions.setdefault(lhs.name, {})[SIGNS[c.head]] = True
    return assumptions


def to_sympy(e, known=()):
    assumptions = sympy_assumptions(known)

    def convert(e):
        if e.is_symbol:
            return sympy.Symbol(e.name, **assumptions.get(e.name, {}))
        if e.is_literal:
            return sympy.Integer(e.value)
        if e.is_constant:
            return CONSTANTS[e]
        return FUNCTIONS[e.head](*map(convert, e.args))

    return convert(e)


def from_sympy(s, kinds):
    if s in NO_VALUE or s.has(*NO_VALUE):
        raise Unrepresentable("no value")
    if s.is_Rational:
        return number(Fraction(int(s.p), int(s.q)))
    if s.is_Symbol:
        return kinds[s.name](s.name)
    if s in BACK_CONSTANTS:
        return BACK_CONSTANTS[s]
    if s.func not in BACK:
        raise Unrepresentable(type(s).__name__)
    args = [from_sympy(a, kinds) for a in s.args]
    if s.func is sympy.Mul:
        args = [f for a in args for f in (a.args if a.head == Mul else (a,))]
    return BACK[s.func](*args)


def ordered(e):
    if e.head is None:
        return e
    args = [ordered(a) for a in e.args]
    if e.head in (Add, Mul, And, Or) and rational(e) is None:
        args.sort(key=key)
    return e.head(*args)


def symbol_kinds(e):
    found, stack = {}, [e]
    while stack:
        e = stack.pop()
        if e.is_symbol:
            found[e.name] = e.kind
        elif e.head is not None:
            stack.extend(e.args)
    return found


def subterms(e):
    stack = [e]
    while stack:
        e = stack.pop()
        yield e
        if e.head is not None:
            stack.extend(e.args)


def sympy_result(e, known=()):
    try:
        theirs = to_sympy(e, known)
    except TypeError as error:
        raise Unrepresentable("SymPy raises") from error
    return from_sympy(theirs, symbol_kinds(e))


def agrees(e, known=()):
    try:
        return ordered(autosimp(e, known)) == ordered(sympy_result(e, known))
    except Unrepresentable:
        return False


def candidate_assumptions(e):
    found = []
    for t in itertools.chain(subterms(e), subterms(autosimp(e))):
        conditions = []
        if t.kind is nr.NumberKind and rational(t) is None and t not in (pi, E, I):
            conditions.append(nr.Ne(t, 0))
        if t.is_symbol and t.kind is nr.NumberKind:
            conditions += [nr.Eq(re(t), t), nr.Gt(t, 0)]
        if t.head is not None and t.head.is_constant and domain(t.head) not in (None, true):
            conditions.append(domain_of(t))
        found += [c for c in conditions if c not in found]
    return found


def assumptions_that_agree(e, given=(), size=2):
    candidates = [c for c in candidate_assumptions(e) if c not in given]
    for n in range(1, size + 1):
        for known in itertools.combinations(candidates, n):
            if agrees(e, (*given, *known)):
                return known
    return None


def classify(e, given=()):
    if agrees(e, given):
        return "same", ()
    known = assumptions_that_agree(e, given)
    if known is not None:
        return "same once assumed", known
    try:
        theirs = sympy_result(e, given)
    except Unrepresentable as reason:
        if str(reason) in ("no value", "SymPy raises"):
            return "different", str(reason)
        return "not yet", str(reason)
    if counterexamples(e, theirs, given):
        return "different", "unsound"
    if ordered(sympy_result(theirs, given)) == ordered(autosimp(e, given)):
        return "different", "SymPy changes its own result"
    return "not yet", ""


def random_expression(rng, depth=3, boolean=False):
    x, y = nr.NumberKind("x"), nr.NumberKind("y")
    if boolean:
        choice = rng.randrange(4)
        if choice == 0 or depth <= 1:
            relation = rng.choice([nr.Eq, nr.Ne, nr.Lt, nr.Gt, nr.Le, nr.Ge])
            return relation(random_expression(rng, depth - 1), random_expression(rng, depth - 1))
        if choice == 1:
            return Not(random_expression(rng, depth - 1, True))
        head = rng.choice([And, Or])
        items = [random_expression(rng, depth - 1, True) for _ in range(rng.randrange(1, 4))]
        return head(*items, *rng.choice([(), (true,), (false,)]))
    if depth <= 0 or rng.random() < 0.25:
        return rng.choice([x, y, x, y, pi, E, I, *map(nr.NumberKind, (-2, -1, 0, 1, 2, 3))])
    sub = lambda: random_expression(rng, depth - 1)
    choice = rng.randrange(10)
    if choice < 3:
        return Add(*(sub() for _ in range(rng.randrange(2, 4))))
    if choice < 6:
        return Mul(*(sub() for _ in range(rng.randrange(2, 4))))
    if choice < 8:
        exponent = rng.choice([nr.NumberKind(rng.randrange(-2, 4)), Pow(2, -1), sub()])
        return Pow(sub(), exponent)
    return rng.choice([sin, cos, tan, exp, log, re])(sub())


def random_expressions(count, seed=0):
    rng = random.Random(seed)
    return [random_expression(rng, 3, rng.random() < 0.15) for _ in range(count)]
