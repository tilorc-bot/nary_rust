"""A temporary stand-in for deciding conditions from facts, to be replaced by reviewed code.

    >>> from nary import Gt, NumberKind
    >>> from nary.deciding._facts import Facts
    >>> x = NumberKind("x")
    >>> Facts([Gt(x, 1)])(Gt(2 * x, 1))
    True
"""

from fractions import Fraction

from .. import arithmetic_rules  # noqa: F401
from .._core import _simplex
from ..arithmetic import Add, Mul, Pow
from ..domains import domain_of
from ..logic import And, Or, true
from ..relational import Eq, Ge, Gt, Le, Lt, Ne, re
from ..rules import is_flat
from ._implications import _symbols, implications

_ORDERS = {Gt: (False, ">"), Ge: (False, ">="), Lt: (True, ">"), Le: (True, ">=")}
_NEGATIONS = {">": "<=", ">=": "<", "=": "!=", "!=": "="}
_RELATIONS = {Eq: "=", Ne: "!="}


def _key(e):
    return e if e.head is None else e.head


def _is_realness(c):
    return c.head == Eq and c.args[0] == re(c.args[1])


def _match(pattern, e, bindings):
    if pattern.is_symbol:
        if bindings.setdefault(pattern, e) != e:
            return None
        return bindings
    if pattern.head is None or e.head is None:
        return bindings if pattern == e else None
    if pattern.head != e.head:
        return None
    patterns, args = pattern.args, e.args
    if is_flat(e.head) and 0 < len(patterns) < len(args):
        last = len(patterns) - 1
        args = (*args[:last], e.head(*args[last:]))
    if len(patterns) != len(args):
        return None
    for p, arg in zip(patterns, args):
        if _match(p, arg, bindings) is None:
            return None
    return bindings


def _instantiate(e, bindings):
    if e.is_symbol:
        return bindings[e]
    if e.head is None:
        return e
    args = [_instantiate(arg, bindings) for arg in e.args]
    return e.head(*args) if not is_flat(e.head) else e.head(*_flattened(e.head(*args)))


def _flattened(e):
    return [part for arg in e.args for part in (_flattened(arg) if arg.head == e.head else (arg,))]


def _indexed():
    realness, about = {}, {}
    for implication in implications:
        c = implication.conclusion
        table, sides = (realness, c.args[1:]) if _is_realness(c) else (about, c.args)
        for side in (side for side in sides if _symbols(side) >= _symbols(c)):
            table.setdefault(_key(side), {}).setdefault(side, []).append(implication)
    return realness, about


_REALNESS, _ABOUT = _indexed()
_DEPTH = 64


class Facts:
    def __init__(self, facts=()):
        self.simplex = _simplex.Simplex()
        self.variables, self.terms, self.linear = {}, {}, {}
        self.real, self.valued = set(), set()
        self.derived, self.true, self.false = set(), set(), set()
        self.depth, self.learned = 0, False
        for fact in facts:
            self._learn(fact)
        for term in list(self.terms.values()):
            self._derive(term)

    def __call__(self, condition):
        if condition in self.true:
            return True
        if condition in self.false or self.depth > _DEPTH:
            return False
        self.depth += 1
        result = self._decide(condition)
        self.depth -= 1
        if self.learned and not self.depth:
            self.false.clear()
            self.learned = False
        (self.true if result else self.false).add(condition)
        return result

    def _decide(self, c):
        if c == true:
            return True
        if c.head == And:
            return all(self(arg) for arg in c.args)
        if c.head == Or:
            return any(self(arg) for arg in c.args)
        if _is_realness(c):
            return self._is_real(c.args[1])
        if c.head == Eq and c.args[0] == c.args[1]:
            return self._has_value(c.args[0])
        if c.head in _ORDERS:
            swap, relation = _ORDERS[c.head]
            lhs, rhs = c.args[::-1] if swap else c.args
            if not (self._is_real(lhs) and self._is_real(rhs)):
                return False
        elif c.head in _RELATIONS:
            lhs, rhs = c.args
            relation = _RELATIONS[c.head]
            if not (self._has_value(lhs) and self._has_value(rhs)):
                return False
        else:
            return False
        form = self._difference(lhs, rhs)
        for var in form[0]:
            self._derive(self.terms[var])
        return self._refutes(form, _NEGATIONS[relation])

    def _refutes(self, form, relation):
        terms, constant = self._encode(form)
        self.simplex.push()
        self.simplex.assert_(terms, relation, constant)
        satisfiable = self.simplex.check()
        self.simplex.pop()
        return not satisfiable

    def _is_real(self, e):
        return e in self.real or all(self._is_real_term(self.terms[var]) for var in self._linear(e)[0])

    def _is_real_term(self, t):
        if t in self.real:
            return True
        for pattern, group in _REALNESS.get(_key(t), {}).items():
            bindings = _match(pattern, t, {})
            if bindings is not None and any(self._apply(i, bindings) for i in group):
                return True
        return False

    def _has_value(self, e):
        return all(self._has_value_term(self.terms[var]) for var in self._linear(e)[0])

    def _has_value_term(self, t):
        if t.head is None or t in self.valued or t in self.real:
            return True
        condition = domain_of(t) if t.head.is_constant else None
        if condition is None or not all(self._has_value(arg) for arg in t.args):
            return False
        if self(condition):
            self.valued.add(t)
            return True
        return False

    def _derive(self, t):
        if t in self.derived:
            return
        self.derived.add(t)
        if t.head == re and self._is_real(t.args[0]):
            self._learn(Eq(t, t.args[0]))
        for pattern, group in _ABOUT.get(_key(t), {}).items():
            bindings = _match(pattern, t, {})
            if bindings is not None:
                for implication in group:
                    self._apply(implication, bindings)

    def _apply(self, implication, bindings):
        if not all(self(_instantiate(p, bindings)) for p in implication.premises):
            return False
        self._learn(_instantiate(implication.conclusion, bindings))
        return True

    def _learn(self, fact):
        self.learned = True
        if fact.head == And:
            for arg in fact.args:
                self._learn(arg)
            return
        if fact.head not in _ORDERS and fact.head not in _RELATIONS:
            return
        lhs, rhs = fact.args
        for side in fact.args:
            self.valued.update(self.terms[var] for var in self._linear(side)[0])
        if _is_realness(fact):
            self._learn_real(rhs)
            if lhs in self.variables:
                self._assert(self._difference(lhs, rhs), "=")
        elif fact.head in _ORDERS:
            swap, relation = _ORDERS[fact.head]
            self._learn_real(lhs)
            self._learn_real(rhs)
            self._assert(self._difference(*(fact.args[::-1] if swap else fact.args)), relation)
        elif fact.head == Eq:
            for one, other in ((lhs, rhs), (rhs, lhs)):
                if not self._linear(one)[0]:
                    self._learn_real(other)
            self._assert(self._difference(lhs, rhs), "=")
        else:
            self._assert(self._difference(lhs, rhs), "!=")

    def _learn_real(self, e):
        self.real.add(e)
        coefficients = self._linear(e)[0]
        nonzero = [var for var, c in coefficients.items() if c]
        if len(nonzero) == 1:
            self.real.add(self.terms[nonzero[0]])

    def _assert(self, form, relation):
        terms, constant = self._encode(form)
        self.simplex.assert_(terms, relation, constant)

    def _encode(self, form):
        coefficients, constant = form
        terms = [(var, c.numerator, c.denominator) for var, c in coefficients.items() if c]
        return terms, (constant.numerator, constant.denominator)

    def _difference(self, lhs, rhs):
        (left, a), (right, b) = self._linear(lhs), self._linear(rhs)
        coefficients = dict(left)
        for var, c in right.items():
            coefficients[var] = coefficients.get(var, 0) - c
        return coefficients, a - b

    def _linear(self, e):
        if e not in self.linear:
            self.linear[e] = self._linearise(e)
        return self.linear[e]

    def _linearise(self, e):
        if e.is_literal:
            return {}, e.value
        if e.head == Add:
            coefficients, constant = {}, 0
            for arg in e.args:
                part, c = self._linear(arg)
                constant += c
                for var, k in part.items():
                    coefficients[var] = coefficients.get(var, 0) + k
            return coefficients, constant
        if e.head == Mul:
            factor, others = 1, []
            for arg in _flattened(e):
                part, c = self._linear(arg)
                if part:
                    others.append(arg)
                else:
                    factor *= c
            if len(others) == 1:
                part, c = self._linear(others[0])
                return {var: factor * k for var, k in part.items()}, factor * c
            if len(others) > 1:
                return {self._variable(Mul(*others)): factor}, 0
            return {}, factor
        if e.head == Pow:
            (base, b), exponent = self._linear(e.args[0]), e.args[1]
            if not base and exponent.is_literal and (b != 0 or exponent.value > 0):
                return {}, Fraction(b) ** exponent.value
        return {self._variable(e): 1}, 0

    def _variable(self, t):
        if t not in self.variables:
            self.variables[t] = self.simplex.variable()
            self.terms[self.variables[t]] = t
        return self.variables[t]
