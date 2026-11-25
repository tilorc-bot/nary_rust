"""Running a catalogue entry through SymPy, to check that SymPy handles it.

``to_sympy(e, assume)`` turns an nary expression into a SymPy one, building
it with SymPy's ordinary constructors, so SymPy's automatic evaluation
happens on the way (``Add(x, 0)`` becomes ``x``). ``assume`` gives the
SymPy assumptions of each symbol by name, such as
``{"x": {"positive": True}}``.

``run(how, expr)`` applies the SymPy call named ``how`` (one of ``CALLS``)
to a SymPy expression. ``"auto"`` is no call at all: the result is what the
constructors gave.

SymPy is only asked what it does. Whether that is right is the business of
``catalogue.numeric``.
"""

import sympy

import nary as nr
from nary import Add, Mul, Pow, cos, exp, log, re, sin, tan
from nary.calculus import Derivative
from nary.functions import is_lambda
from nary.logic import And, Not, Or, false, true

__all__ = ["CALLS", "SYMPY_COMMIT", "SYMPY_VERSION", "run", "to_sympy"]

# The SymPy version the catalogue was checked against. tests/test_catalogue.py
# refuses to run the SymPy checks with any other.
SYMPY_VERSION = "1.14.0"

# The commit of that release in github.com/sympy/sympy: the target of the
# annotated tag sympy-1.14.0, "release sympy 1.14.0 final". Links to SymPy's
# tests point at it.
SYMPY_COMMIT = "16fa855354eb7bcabd3fe10993841e03b1382692"

CALLS = {
    "auto": lambda e: e,
    "simplify": sympy.simplify,
    "expand": sympy.expand,
    "factor": sympy.factor,
    "cancel": sympy.cancel,
    "together": sympy.together,
    "trigsimp": sympy.trigsimp,
    "expand_trig": sympy.expand_trig,
    "powsimp": sympy.powsimp,
    "powdenest": sympy.powdenest,
    "expand_log": sympy.expand_log,
    "logcombine": sympy.logcombine,
    "expand_power_base": sympy.expand_power_base,
    "expand_power_exp": sympy.expand_power_exp,
    "simplify_logic": sympy.simplify_logic,
    "to_nnf": sympy.to_nnf,
    "doit": lambda e: e.doit(),
    "expand_multinomial": sympy.expand_multinomial,
    "rewrite_exp": lambda e: e.rewrite(sympy.exp),
}

_FUNCTIONS = {
    Add: sympy.Add,
    Mul: sympy.Mul,
    Pow: sympy.Pow,
    sin: sympy.sin,
    cos: sympy.cos,
    tan: sympy.tan,
    exp: sympy.exp,
    log: sympy.log,
    re: sympy.re,
    nr.Eq: sympy.Eq,
    nr.Ne: sympy.Ne,
    nr.Lt: sympy.Lt,
    nr.Gt: sympy.Gt,
    nr.Le: sympy.Le,
    nr.Ge: sympy.Ge,
    And: sympy.And,
    Or: sympy.Or,
    Not: sympy.Not,
}

_CONSTANTS = {
    nr.pi: sympy.pi,
    nr.E: sympy.E,
    nr.I: sympy.I,
    true: sympy.true,
    false: sympy.false,
}


def run(how, expr):
    """``expr`` after the SymPy call named ``how``."""
    return CALLS[how](expr)


def to_sympy(e, assume=None):
    """The SymPy expression for the nary expression ``e``."""
    return _Converter(assume or {}).convert(e)


class _Converter:
    def __init__(self, assume):
        self.assume = assume
        self.bound = {}

    def symbol(self, e):
        if e.name in self.bound:
            return self.bound[e.name]
        if e.kind is nr.NumberKind:
            return sympy.Symbol(e.name, **self.assume.get(e.name, {}))
        if e.kind is nr.BoolKind:
            return sympy.Symbol(e.name)
        raise ValueError(f"no SymPy symbol for {e!r} of kind {e.kind!r}")

    def function(self, f, argument):
        """The SymPy expression for ``f(argument)``, ``f`` a function
        expression."""
        if f.is_constant and f in _FUNCTIONS:
            return _FUNCTIONS[f](argument)
        if is_lambda(f):
            *variables, body = f.args
            (variable,) = variables
            return sympy.Lambda(self.symbol(variable), self.convert(body))(argument)
        if f.head == Derivative:
            (g,) = f.args
            t = sympy.Dummy("t")
            body = self.function(g, t)
            derivative = sympy.Derivative(body, t)
            if isinstance(argument, sympy.Symbol):
                return derivative.subs(t, argument)
            return sympy.Subs(derivative, t, argument)
        raise ValueError(f"no SymPy function for {f!r}")

    def convert(self, e):
        if e.is_symbol:
            return self.symbol(e)
        if e.is_literal:
            return sympy.Integer(e.value)
        if e.is_constant:
            return _CONSTANTS[e]
        if e.head in _FUNCTIONS:
            return _FUNCTIONS[e.head](*(self.convert(a) for a in e.args))
        (arg,) = e.args
        return self.function(e.head, self.convert(arg))
