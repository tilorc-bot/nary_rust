"""Translating the expressions of a SymPy test into nary, and SymPy's values
back into nary.

``Translator.value(node)`` reads a Python expression of the test (an ``ast``
node) and builds the nary expression it writes, without evaluating
anything: names are bound to nary's objects and the arithmetic operators are
nary's own (``x**0`` is ``Pow(x, 0)``, ``1/x`` is ``Mul(1, Pow(x, -1))``,
``x - 1`` is ``Add(x, Mul(-1, 1))``, as for the hand-written entries). Only
arithmetic on two Python ints is done, by Python, as it is when the test
runs (``123712**12 - 1``; ``1/2`` is a float). The names and functions it
knows are the tables of ``catalogue.from_tests.rules``.

The result is a ``V``: the nary expression (or an ``int``, or ``Missing``
for something nary cannot write, which propagates so that every missing
piece is named), and the assumptions of the symbols in it, by name. A
construct the translator cannot follow raises ``NotTranslatable``.

``from_sympy(value)`` turns a SymPy expression (SymPy's evaluated result)
into nary, in SymPy's argument order.
"""

import ast
from dataclasses import dataclass, field

import sympy

import nary as nr
from nary import Add, Mul, Pow, cos, exp, log, sin, tan

from ..entry import ASSUMPTIONS, NO_CONDITION
from . import rules

__all__ = ["Missing", "NotTranslatable", "Translator", "V", "from_sympy", "rational"]


class NotTranslatable(Exception):
    """The generator cannot follow this; the message says what."""


@dataclass(frozen=True)
class Missing:
    """Something nary cannot write; ``labels`` name what is missing."""
    labels: frozenset


@dataclass
class V:
    expr: object
    assume: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Helper:
    """A name bound by a def or class inside the test function."""
    name: str


@dataclass(frozen=True)
class Unknown:
    """A name whose value the generator does not know; ``reason`` says why,
    and ``category`` is what an assert using it is (``not-translatable``, or
    ``not-a-simplification`` for a value that came from a query)."""
    category: str
    reason: str


def merge(*maps):
    """The assumptions of several values together; two symbols with the same
    name and different assumptions cannot be told apart in nary."""
    out = {}
    for m in maps:
        for name, facts in m.items():
            if name in out and out[name] != facts:
                raise NotTranslatable(f"two symbols named {name} with different assumptions")
            out[name] = facts
    return out


def missing(*labels):
    return Missing(frozenset(labels))


def rational(p, q=1):
    """``p/q`` as the catalogue writes it: Pow(q, -1) for 1/q, Mul(p, Pow(q, -1))
    otherwise, an integer literal for q = 1."""
    r = sympy.Rational(p, q)
    if r.q == 1:
        return nr.NumberKind(int(r.p))
    inverse = Pow(nr.NumberKind(int(r.q)), -1)
    return inverse if r.p == 1 else Mul(nr.NumberKind(int(r.p)), inverse)


def _number(v):
    """A Python int as an nary literal; anything else unchanged."""
    return nr.NumberKind(v) if isinstance(v, int) and not isinstance(v, bool) else v


def _combine(f, values):
    """``f`` applied to the expressions of ``values``, with Missing propagated."""
    if any(isinstance(v.expr, tuple) for v in values):
        raise NotTranslatable("arithmetic on a tuple of symbols")
    assume = merge(*(v.assume for v in values))
    gone = [v.expr for v in values if isinstance(v.expr, Missing)]
    if gone:
        return V(Missing(frozenset().union(*(g.labels for g in gone))), assume)
    return V(f(*(v.expr for v in values)), assume)


def symbol(name, facts):
    """A number symbol with SymPy assumptions ``facts`` (a dict)."""
    for fact in facts.items():
        if fact not in ASSUMPTIONS and fact not in NO_CONDITION:
            return V(missing(f"assumption {fact[0]}={fact[1]}"), {name: dict(facts)})
    if not name.isidentifier():
        raise NotTranslatable(f"the symbol name {name!r} is not an identifier")
    return V(nr.NumberKind(name), {name: dict(facts)})


_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
}

_NARY_FUNCTIONS = {"exp": exp, "log": log, "sin": sin, "cos": cos, "tan": tan}


class Translator:
    """Translates the expressions of one test function. ``env`` maps local
    names to ``V``, ``Helper`` or ``Unknown``; ``module`` is the namespace of
    the test module (for its module-level symbols)."""

    def __init__(self, module, env):
        self.module = module
        self.env = env

    # -- names ------------------------------------------------------------

    def name(self, node):
        name = node.id
        if name in self.env:
            bound = self.env[name]
            if isinstance(bound, Helper):
                raise NotTranslatable(f"uses {name}, defined in the test")
            if isinstance(bound, Unknown):
                raise NotTranslatable(bound.reason)
            return bound
        value = self.module.get(name)
        if isinstance(value, sympy.Symbol):
            return symbol(value.name, value._assumptions_orig)
        if name in ("I", "pi", "E"):
            return V(getattr(nr, name))
        if name in rules.OUT_OF_VOCABULARY:
            return V(missing(rules.OUT_OF_VOCABULARY[name]))
        raise NotTranslatable(f"uses {name}, which the generator does not translate")

    # -- expressions ----------------------------------------------------------

    def value(self, node):
        method = getattr(self, "_" + type(node).__name__, None)
        if method is None:
            raise NotTranslatable(f"a {type(node).__name__} expression")
        return method(node)

    def _Name(self, node):
        return self.name(node)

    def _Constant(self, node):
        v = node.value
        if isinstance(v, bool):
            return V(missing("Python bools"))
        if isinstance(v, int):
            return V(v)
        if isinstance(v, float):
            return V(missing("floats"))
        raise NotTranslatable(f"a {type(v).__name__} constant")

    def _BinOp(self, node):
        op = type(node.op)
        if op not in _BINOPS:
            raise NotTranslatable(f"the operator {op.__name__}")
        a, b = self.value(node.left), self.value(node.right)
        if isinstance(a.expr, int) and isinstance(b.expr, int):
            # Python arithmetic on two Python ints, as when the test runs.
            if op is ast.Div or (op is ast.Pow and b.expr < 0):
                return V(missing("floats"))
            return V(_BINOPS[op](a.expr, b.expr))
        return _combine(lambda x, y: _BINOPS[op](_number(x), _number(y)), [a, b])

    def _UnaryOp(self, node):
        a = self.value(node.operand)
        if isinstance(node.op, ast.UAdd):
            return a
        if isinstance(node.op, ast.USub):
            return _combine(lambda x: -x, [a])
        raise NotTranslatable(f"the operator {type(node.op).__name__}")

    def _Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == "S" and "S" not in self.env:
            spec = rules.S_ATTRIBUTES.get(node.attr)
            if spec is None:
                raise NotTranslatable(f"S.{node.attr}")
            if spec[0] == "rational":
                return V(rational(spec[1], spec[2]))
            if spec[0] == "int":
                return V(nr.NumberKind(spec[1]))
            if spec[0] == "missing":
                return V(missing(spec[1]))
            return V(getattr(nr, spec[0]))
        raise NotTranslatable(f"the attribute .{node.attr}")

    def _Call(self, node):
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr in rules.METHODS:
                category, label = rules.METHODS[func.attr]
                if category == "out-of-vocabulary":
                    self.value(func.value)
                    return V(missing(label))
                raise NotTranslatable(label)
            raise NotTranslatable(f"a method call (.{func.attr}) inside an operand")
        if not isinstance(func, ast.Name):
            raise NotTranslatable("a call of a computed function")
        name = func.id
        if name in self.env:
            self.name(func)  # raises for helpers and unknowns
            raise NotTranslatable(f"calls {name}, bound in the test")
        if name in rules.OUT_OF_VOCABULARY:
            for a in node.args:
                self._maybe(a)
            return V(missing(rules.OUT_OF_VOCABULARY[name]))
        if name not in rules.FUNCTIONS:
            raise NotTranslatable(f"calls {name}, which the generator does not translate")
        keywords = {k.arg: k.value for k in node.keywords}
        if name in ("Symbol", "symbols"):
            return self._symbols(name, node.args, keywords)
        if name in ("Pow", "Mul", "Add") and set(keywords) <= {"evaluate"}:
            keywords = {}  # nary is inert: evaluate=False changes nothing
        if keywords:
            raise NotTranslatable(f"{name} with keyword arguments")
        args = [self.value(a) for a in node.args]
        return self._function(name, args)

    def _maybe(self, node):
        """Translate ``node`` only to find a NotTranslatable in it."""
        self.value(node)

    def _function(self, name, args):
        ints = all(isinstance(a.expr, int) for a in args)
        if name == "Rational":
            if ints and len(args) in (1, 2):
                return V(rational(*(a.expr for a in args)))
            raise NotTranslatable("Rational of something other than Python ints")
        if name in ("Integer", "Number", "S"):
            # A SymPy integer, not a Python int: no Python arithmetic on it.
            if len(args) == 1 and isinstance(args[0].expr, int):
                return V(nr.NumberKind(args[0].expr))
            if name == "S" and len(args) == 1:
                return args[0]
            raise NotTranslatable(f"{name} of something other than a Python int")
        if name == "sqrt" and len(args) == 1:
            return _combine(lambda e: Pow(_number(e), rational(1, 2)), args)
        if name == "cbrt" and len(args) == 1:
            return _combine(lambda e: Pow(_number(e), rational(1, 3)), args)
        if name == "root":
            if len(args) == 2 and isinstance(args[1].expr, int):
                k = args[1].expr
                return _combine(lambda e: Pow(_number(e), rational(1, k)), args[:1])
            raise NotTranslatable("root with an index other than a Python int")
        if name in _NARY_FUNCTIONS and len(args) == 1:
            f = _NARY_FUNCTIONS[name]
            return _combine(lambda e: f(_number(e)), args)
        if name in ("Pow", "power") and len(args) == 2:
            return _combine(lambda b, e: Pow(_number(b), _number(e)), args)
        if name in ("Mul", "Add"):
            f = Mul if name == "Mul" else Add
            return _combine(lambda *es: f(*(_number(e) for e in es)), args)
        raise NotTranslatable(f"{name} with {len(args)} arguments")

    def _symbols(self, name, args, keywords):
        if not (args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str)
                and len(args) == 1):
            raise NotTranslatable(f"{name} without a literal name")
        facts = {}
        for key, value in keywords.items():
            if not (isinstance(value, ast.Constant) and isinstance(value.value, bool)):
                raise NotTranslatable(f"{name} with a computed assumption")
            facts[key] = value.value
        if name == "Symbol":
            return symbol(args[0].value, facts)
        made = sympy.symbols(args[0].value)
        if isinstance(made, sympy.Symbol):
            return symbol(made.name, facts)
        if not (isinstance(made, tuple) and all(isinstance(m, sympy.Symbol) for m in made)):
            raise NotTranslatable("symbols with a range or a nested name")
        return V(tuple(symbol(m.name, facts) for m in made))


# ---- SymPy's values back into nary -----------------------------------------

_FROM_SYMPY_FUNCTIONS = {sympy.exp: exp, sympy.log: log, sympy.sin: sin, sympy.cos: cos,
                         sympy.tan: tan}


def from_sympy(e):
    """The nary expression for the SymPy expression ``e``, as a ``V``."""
    if isinstance(e, sympy.Symbol) and not isinstance(e, sympy.Dummy):
        return symbol(e.name, e._assumptions_orig)
    if e is sympy.I:
        return V(nr.I)
    if e is sympy.pi:
        return V(nr.pi)
    if e is sympy.E:
        return V(nr.E)
    if isinstance(e, sympy.Integer):
        return V(nr.NumberKind(int(e)))
    if isinstance(e, sympy.Rational):
        return V(rational(int(e.p), int(e.q)))
    if isinstance(e, sympy.Float):
        return V(missing("floats"))
    if e in (sympy.oo, -sympy.oo, sympy.zoo):
        return V(missing("infinities"))
    if e is sympy.nan:
        return V(missing("nan"))
    if isinstance(e, (sympy.Add, sympy.Mul, sympy.Pow)):
        f = {sympy.Add: Add, sympy.Mul: Mul, sympy.Pow: Pow}[type(e)]
        return _combine(f, [from_sympy(a) for a in e.args])
    if type(e) in _FROM_SYMPY_FUNCTIONS and len(e.args) == 1:
        f = _FROM_SYMPY_FUNCTIONS[type(e)]
        return _combine(f, [from_sympy(e.args[0])])
    if isinstance(e, sympy.Order):
        return V(missing("series"))
    if isinstance(e, sympy.Abs):
        return V(missing("Abs"))
    if isinstance(e, sympy.Basic):
        return V(missing(type(e).__name__))
    raise NotTranslatable(f"SymPy's value is a {type(e).__name__}, not an expression")
