"""Running a SymPy test file with nary's expressions in place of SymPy's.

``collect(path)`` returns the cases of the test file: one per ``==`` or
``!=`` that an assert makes each time it runs, with both sides as nary
expressions, or with the reason there are none.

The test's own code is run, by Python. Two things are changed first:

- Every name the test file takes from SymPy stands for a ``Value``: an nary
  expression, or the reasons nary has none. ``x`` is nary's ``x``,
  ``Rational(1, 2)`` is ``Pow(2, -1)``, ``sqrt(x)`` is ``Pow(x, Pow(2, -1))``.
  nary's expressions are inert, so each side is the expression as the test
  wrote it. A name nary does not have (``oo``, ``Float``) and an attribute
  of an expression (``.is_real``, ``.expand()``) give a ``Value`` with a
  reason from ``rules.name``, and anything computed from it keeps the
  reason.
- Each ``assert`` is replaced by a call that records its operands and never
  fails, and every other statement inside a test function is run so that an
  error in it gives the names it binds the reason, and the test goes on.

An assert that is never reached still gets a case, with the reason.
"""

import ast
import importlib
import operator
import re
from dataclasses import dataclass, field
from pathlib import Path

import sympy

import nary as nr

from catalogue.entry import ASSUMPTIONS

from . import rules
from .rules import MISSING, NOT_APPLICABLE, NOT_RUN

__all__ = ["Case", "collect"]

# SymPy assumptions that say nothing in nary, where every number symbol is a
# complex number.
NO_CONDITION = {("complex", True)}


# ---- values ----------------------------------------------------------------


class Unknown(Exception):
    """Python needed a definite answer (a truth value, the items) from a
    ``Value`` that has none."""

    def __init__(self, why):
        super().__init__(", ".join(sorted(label for _, label in why)))
        self.why = why


class Value:
    """An nary expression (``expr``) and the SymPy assumptions of its
    symbols by name (``assume``), or the reasons there is none (``why``, a
    set of ``(pile, label)``)."""

    __slots__ = ("expr", "why", "assume")

    def __init__(self, expr=None, why=(), assume=None):
        self.expr, self.why, self.assume = expr, frozenset(why), assume or {}

    def __getattr__(self, attribute):
        if attribute.startswith("__"):
            raise AttributeError(attribute)
        return Value(why=self.why | {rules.name(attribute)})

    def __call__(self, *args, **keywords):
        if self.expr is not None:
            raise TypeError(f"{self!r} is not a function")
        return Value(why=self.why.union(*(a.why for a in (*args, *keywords.values())
                                          if isinstance(a, Value))))

    def __getitem__(self, key):
        if self.expr is not None:
            raise TypeError(f"{self!r} has no items")
        return self

    def __bool__(self):
        if self.expr is None:
            raise Unknown(self.why)
        return True

    def __iter__(self):
        raise Unknown(self.why or {(NOT_RUN, "iterating over an expression")})

    def __eq__(self, other):
        return isinstance(other, Value) and self.expr is not None and self.expr == other.expr

    def __hash__(self):
        return hash(self.expr)

    def __repr__(self):
        return repr(self.expr) if self.expr is not None else f"<no value: {Unknown(self.why)}>"

    def __abs__(self):
        return Value(why=self.why | {(MISSING, "Abs")})

    def __pos__(self):
        return self

    def __neg__(self):
        return apply(operator.neg, self)

    def _inequality(self, other):
        return Value(why=self.why | {(NOT_APPLICABLE, "an inequality (a truth value)")})

    __lt__ = __le__ = __gt__ = __ge__ = _inequality

    def __enter__(self):
        return self

    def __exit__(self, *error):
        return False


for _name in ("add", "sub", "mul", "truediv", "pow"):
    _f = getattr(operator, _name)
    setattr(Value, f"__{_name}__", lambda a, b, f=_f: apply(f, a, b))
    setattr(Value, f"__r{_name}__", lambda a, b, f=_f: apply(f, b, a))


def lift(v):
    """``v`` as a ``Value``: a Python int is a literal, as when the test
    runs in SymPy."""
    if isinstance(v, Value):
        return v
    if type(v) is int:
        return Value(nr.NumberKind(v))
    if isinstance(v, float):
        return Value(why={(MISSING, "floats")})
    return Value(why={(NOT_RUN, f"a Python {type(v).__name__} where an expression is expected")})


def together(*values):
    """``(why, assume)`` of several values together. Two symbols with one
    name and different assumptions are a reason: nary could not tell them
    apart."""
    why, assume = frozenset().union(*(v.why for v in values)), {}
    for v in values:
        for name, facts in v.assume.items():
            if assume.setdefault(name, facts) != facts:
                why |= {(NOT_RUN, f"two symbols named {name} with different assumptions")}
    return why, assume


def apply(f, *args):
    """``f`` of the expressions of ``args``, or their reasons together."""
    args = [lift(a) for a in args]
    why, assume = together(*args)
    return Value(why=why) if why else Value(f(*(a.expr for a in args)), assume=assume)


def _function(f):
    # evaluate=False is dropped: nary's expressions are inert anyway.
    return lambda *args, evaluate=None: apply(f, *args)


def _rational(p, q=1):
    """``p/q`` as the catalogue writes it: ``Pow(q, -1)`` for 1/q, ``Mul(p,
    Pow(q, -1))`` otherwise, a literal when it is an integer."""
    if type(p) is not int or type(q) is not int:
        return Value(why={(NOT_RUN, "Rational of something other than Python ints")})
    r = sympy.Rational(p, q)
    if r.q == 1:
        return lift(int(r.p))
    inverse = nr.Pow(nr.NumberKind(int(r.q)), -1)
    return Value(inverse if r.p == 1 else nr.Mul(nr.NumberKind(int(r.p)), inverse))


def _root(k):
    return lambda v, evaluate=None: apply(lambda e: nr.Pow(e, _rational(1, k).expr), v)


def _symbol(name, **facts):
    for fact in facts.items():
        if fact not in ASSUMPTIONS and fact not in NO_CONDITION:
            label = f"assumption {fact[0]}={fact[1]}" if isinstance(fact[1], bool) \
                else f"Symbol with {fact[0]}="
            return Value(why={(MISSING, label)})
    return Value(nr.NumberKind(name), assume={name: dict(sorted(facts.items()))})


def _symbols(names, **facts):
    made = sympy.symbols(names)
    if isinstance(made, sympy.Symbol):
        return _symbol(made.name, **facts)
    return tuple(_symbol(s.name, **facts) for s in made)


class _S:
    """SymPy's ``S``: ``S(2)`` and ``S.Half``."""
    Zero, One, NegativeOne, Half = lift(0), lift(1), lift(-1), _rational(1, 2)
    ImaginaryUnit, Exp1, Pi = Value(nr.I), Value(nr.E), Value(nr.pi)

    def __call__(self, v):
        return lift(v)

    def __getattr__(self, attribute):
        return Value(why={rules.name(attribute)})


# What stands for each SymPy object that nary has.
_SHIMS = [
    (sympy.S, _S()), (sympy.I, _S.ImaginaryUnit), (sympy.E, _S.Exp1), (sympy.pi, _S.Pi),
    (sympy.Rational, _rational), (sympy.Integer, lift), (sympy.Number, lift),
    (sympy.sqrt, _root(2)), (sympy.cbrt, _root(3)),
    (sympy.root, lambda v, k: _root(k)(v) if type(k) is int else Value(why={(MISSING, "root")})),
    (sympy.Add, _function(nr.Add)), (sympy.Mul, _function(nr.Mul)),
    (sympy.Pow, _function(nr.Pow)), (sympy.exp, _function(nr.exp)),
    (sympy.log, _function(nr.log)), (sympy.sin, _function(nr.sin)),
    (sympy.cos, _function(nr.cos)), (sympy.tan, _function(nr.tan)),
    (sympy.Symbol, _symbol), (sympy.symbols, _symbols),
]


def shim(name, obj):
    """What stands for the object ``obj`` that the test file calls ``name``."""
    for target, replacement in _SHIMS:
        if obj is target:
            return replacement
    if isinstance(obj, sympy.Symbol):
        return _symbol(obj.name, **obj._assumptions_orig)
    module = getattr(obj, "__module__", None) or type(obj).__module__
    if name in rules.NOT_VALUES or isinstance(obj, sympy.Basic) or module.startswith("sympy"):
        return Value(why={rules.name(name)})
    return obj


# ---- the test file, rewritten ----------------------------------------------

_EQUAL = {ast.Eq: "==", ast.Is: "==", ast.NotEq: "!=", ast.IsNot: "!="}
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.ListComp,
           ast.SetComp, ast.DictComp, ast.GeneratorExp)
_PLAIN = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Assert, ast.Return, ast.Pass, ast.Break,
          ast.Continue, ast.Global, ast.Nonlocal)


def _bound(node):
    """The names a statement binds in its own scope."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, _SCOPES):
        return set()
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        return {node.id}
    if isinstance(node, ast.alias):
        return {(node.asname or node.name).split(".")[0]}
    return set().union(*(_bound(child) for child in ast.iter_child_nodes(node)))


@dataclass
class _Site:
    """An assert statement: where it is, its text, and the comparisons it
    makes between consecutive operands (none when it is not a chain of
    ``==`` and ``!=``)."""
    function: str
    line: int
    end_line: int
    position: int
    source: str
    ops: tuple


class _Rewriter(ast.NodeTransformer):
    def __init__(self):
        self.sites = []
        self.function = None

    def visit(self, node):
        top = self.function is None and isinstance(node, ast.FunctionDef)
        if top:
            self.function = node.name
            node.decorator_list = []
        new = super().visit(node)
        if top:
            self.function = None
        elif self.function and isinstance(node, ast.stmt) and not isinstance(node, _PLAIN):
            new = self._guarded(node, new)
        return new

    def visit_Assert(self, node):
        test, negated = node.test, False
        while isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            test, negated = test.operand, not negated
        operands, ops = [test], ()
        if isinstance(test, ast.Compare) and all(type(op) in _EQUAL for op in test.ops):
            operands = [test.left, *test.comparators]
            ops = tuple(_EQUAL[type(op)] for op in test.ops)
            if negated and len(ops) == 1:
                ops = ("!=" if ops == ("==",) else "==",)
            elif negated:
                operands, ops = [test], ()
        position = sum(s.line == node.lineno for s in self.sites)
        self.sites.append(_Site(self.function or "<module>", node.lineno, node.end_lineno,
                                position, ast.unparse(node.test), ops))
        thunk = ast.Lambda(ast.arguments([], [], None, [], [], None, []),
                           ast.Tuple(operands, ast.Load()))
        return ast.Expr(_call("_sb_case", ast.Constant(len(self.sites) - 1), thunk))

    def _guarded(self, node, new):
        """``new`` (the statement ``node``, rewritten) in a ``try`` that, on
        an error, gives the names it binds the reason."""
        body = [new]
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            body += [ast.Assign([ast.Name(n, ast.Store())],
                                _call("_sb_shim", ast.Constant(n), ast.Name(n, ast.Load())))
                     for n in sorted(_bound(node))]
        failed = _call("_sb_fail", ast.Constant(node.lineno), ast.Constant(node.end_lineno),
                       ast.Name("_sb_error", ast.Load()))
        names = [ast.Name(n, ast.Store()) for n in sorted(_bound(node))]
        handler = ast.ExceptHandler(ast.Name("Exception", ast.Load()), "_sb_error",
                                    [ast.Assign(names, failed) if names else ast.Expr(failed)])
        return ast.Try(body, [handler], [], [])


def _call(function, *args):
    return ast.Call(ast.Name(function, ast.Load()), list(args), [])


# ---- running ---------------------------------------------------------------


@dataclass(frozen=True)
class Case:
    """One comparison of one run of an assert. ``left op right`` with
    ``op`` ``"=="`` or ``"!="`` and the SymPy assumptions of the symbols in
    ``assume``; or, when there are no two nary expressions to compare,
    ``pile`` and ``reason`` say why. ``index`` counts the cases of one
    assert (a chain, or an assert in a loop)."""
    function: str
    line: int
    end_line: int
    position: int
    index: int
    source: str
    op: str = None
    left: nr.Expr = None
    right: nr.Expr = None
    assume: dict = field(default_factory=dict, hash=False)
    pile: str = None
    reason: str = ""

    @property
    def id(self):
        return (f"{self.function}:L{self.line}" + (f".{self.position}" if self.position else "")
                + (f"#{self.index}" if self.index else ""))


def _unscored(why):
    """``(pile, reason)`` for a case with the reasons ``why``: not a test of
    a value if any reason says so, else what nary is missing, else what the
    scoreboard could not do."""
    for pile in (NOT_APPLICABLE, MISSING, NOT_RUN):
        labels = sorted(label for p, label in why if p == pile)
        if labels:
            return pile, ("needs " if pile == MISSING else "") + ", ".join(labels)


def _error(error):
    if isinstance(error, Unknown):
        return error.why
    text = re.sub(r" at 0x[0-9a-f]+", "", f"{type(error).__name__}: {error}")
    return frozenset({(NOT_RUN, text[:120])})


class _Run:
    def __init__(self, sites):
        self.sites = sites
        self.cases = []
        self.failed = []   # (first line, last line, why) of statements that raised

    def case(self, number, thunk):
        site = self.sites[number]
        try:
            operands = thunk()
        except Exception as error:  # noqa: BLE001 - any error is a reason
            return self.add(site, why=_error(error))
        if not site.ops:
            (v,) = operands
            return self.add(site, why=isinstance(v, Value) and v.why or {
                (NOT_RUN, "not a chain of == and != (an and/or, an in, a call)")})
        for op, left, right in zip(site.ops, operands, operands[1:]):
            self.compare(site, op, left, right)

    def compare(self, site, op, left, right):
        if (isinstance(left, (list, tuple)) and isinstance(right, (list, tuple))
                and len(left) == len(right)):
            for pair in zip(left, right):  # item by item
                self.compare(site, op, *pair)
            return
        # A reason one side carries says more than "compared with True".
        why = frozenset().union(*(v.why for v in (left, right) if isinstance(v, Value)))
        for v in (left, right):
            if not why and isinstance(v, (bool, str, type(None))):
                why = {(NOT_APPLICABLE, f"compares with a Python {type(v).__name__}")}
        left, right = lift(left), lift(right)
        more, assume = together(left, right)
        if why or more:
            self.add(site, why=why or more)
        else:
            self.add(site, op=op, left=left.expr, right=right.expr,
                     assume={name: facts for name, facts in sorted(assume.items()) if facts})

    def add(self, site, why=None, **fields):
        if why:
            fields["pile"], fields["reason"] = _unscored(why)
        index = sum(c.function == site.function and c.line == site.line
                    and c.position == site.position for c in self.cases)
        self.cases.append(Case(site.function, site.line, site.end_line, site.position, index,
                               site.source, **fields))

    def fail(self, line, end_line, error):
        why = _error(error)
        self.failed.append((line, end_line, why))
        return Value(why=why)

    def not_reached(self, stopped):
        """A case for each assert that never ran, with the reason: the
        innermost statement around it that raised, or what stopped its test
        function."""
        for site in self.sites:
            if any((c.function, c.line, c.position) == (site.function, site.line, site.position)
                   for c in self.cases):
                continue
            around = [(end - first, why) for first, end, why in self.failed
                      if first <= site.line <= end]
            why = min(around, key=lambda a: a[0])[1] if around else stopped.get(site.function)
            reason = "not reached" + (f": {_unscored(why)[1]}" if why else "")
            self.add(site, why={(NOT_RUN, reason)})


def source(path):
    """The bytes of the installed SymPy's file at ``path`` (a path in the
    SymPy repository)."""
    module = importlib.import_module(path.removesuffix(".py").replace("/", "."))
    return Path(module.__file__).read_bytes()


def collect(path):
    """The cases of the SymPy test file at ``path``, in the order of the
    file."""
    rewriter = _Rewriter()
    tree = ast.fix_missing_locations(rewriter.visit(ast.parse(source(path))))
    namespace = {"__name__": "scoreboard"}
    exec(compile(tree, path, "exec"), namespace)
    run = _Run(rewriter.sites)
    tests = [name for name, obj in namespace.items()
             if name.startswith("test_") and callable(obj)]
    for name, obj in list(namespace.items()):
        if not name.startswith("__") and name not in tests:
            namespace[name] = shim(name, obj)
    namespace.update({name: Value(why={rules.name(name)}) for name in rules.NOT_VALUES},
                     _sb_case=run.case, _sb_fail=run.fail, _sb_shim=shim)
    stopped = {}
    for name in tests:
        try:
            namespace[name]()
        except Exception as error:  # noqa: BLE001
            stopped[name] = _error(error)
    run.not_reached(stopped)
    return sorted(run.cases, key=lambda c: (c.line, c.position, c.index))
