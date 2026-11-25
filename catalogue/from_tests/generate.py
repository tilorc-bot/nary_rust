"""The generator: SymPy's test file -> ledger and catalogue entries.

``python -m catalogue.from_tests`` runs ``write()``, which writes, for each
file of ``rules.FILES`` (today only ``power``), ``<stem>.py`` (the ledger,
the generated entries and the links to hand-written entries) and
``<stem>.md`` (the same as a table with permalinks).
``tests/test_from_tests.py`` regenerates both and fails on any difference.

How it works, for one test file:

1. The file of the installed SymPy is parsed with ``ast`` (its git blob sha
   must be the one in ``rules.FILES``), and the module is imported for its
   module-level names (``x``, ``Rational``, ...).
2. Each top-level test function is walked statement by statement, keeping
   two scopes: a SymPy scope (the module's names, plus each simple
   assignment of the function executed with real SymPy) and an nary
   environment (each assignment translated by ``translate.Translator``).
   Loops, branches, ``with``, ``try`` and nested definitions are never run:
   their asserts are ``not-translatable`` and the names they bind are
   unknown.
3. Each assert is classified in the order given in ``rules`` (first match
   wins). For ``assert A == B`` (or ``A == B == C``, or ``is``), each
   operand is translated into nary *as written*, without evaluating it
   (``x**0`` is ``Pow(x, 0)``), and the expected value is the last operand
   evaluated by SymPy, turned back into nary by ``translate.from_sympy``.
   An outermost call in ``rules.CALL_METHODS``/``CALL_FUNCTIONS``
   (``.expand()``, ``.rewrite(exp)``, ``expand_multinomial``) is split off:
   the receiver is the input and the call is how SymPy makes the entry.
4. Every operand but the last whose written form differs from the expected
   value (up to the order of Add and Mul arguments,
   ``catalogue.engine.normal``) is a candidate entry; the last operand is
   the test's way of writing the value and is a candidate only when no
   other operand is (``assert 2 + I == sqrt(3 + 4*I)``). It is checked: SymPy, given the nary form with the
   symbols' assumptions, must give the expected value (with ``"auto"``
   when no call is needed), and ``catalogue.numeric.check`` decides the
   status: wrong values -> rejected, only definedness -> undecided with a
   class from ``rules.UNDECIDED_CLASSES`` found by ``cause``, else accepted.
5. Identical candidates (same input, expected, call and assumptions) are
   one entry with several sources. A candidate equal to a hand-written
   entry (up to argument order) is not generated: the hand-written entry
   gains the source (``LINKS``).

Nothing here is a judgement about a particular assert: those are the
tables of ``rules``.
"""

import ast
import hashlib
import importlib
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path

import sympy

import nary as nr

from .. import numeric
from ..engine import normal
from ..entry import Source, generated
from ..sympy_check import SYMPY_COMMIT, run, to_sympy
from . import rules
from .ledger import Row
from .translate import Helper, Missing, NotTranslatable, Translator, Unknown, V, from_sympy, merge

__all__ = ["Generated", "cause", "generate", "render", "write"]

HERE = Path(__file__).resolve().parent


def git_blob_sha(data):
    """The git blob sha of ``data`` (bytes), as ``git hash-object`` gives."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def module_name(path):
    """``sympy/core/tests/test_power.py`` -> ``sympy.core.tests.test_power``."""
    return path.removesuffix(".py").replace("/", ".")


# ---- the classification of one assert --------------------------------------


class Classified(Exception):
    """The assert's category is decided; ``reason`` says why."""

    def __init__(self, category, reason):
        super().__init__(reason)
        self.category = category
        self.reason = reason


def query_reason(node, env):
    """The reason ``node`` (an expression of the test) is a query rather than
    a value, or None: the first marker in a pre-order walk."""
    for sub in _preorder(node):
        if isinstance(sub, ast.Attribute):
            reason = rules.is_query_attribute(sub.attr)
            if reason:
                return reason
        elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
            if sub.func.id in rules.QUERY_CALLS and sub.func.id not in env:
                return rules.QUERY_CALLS[sub.func.id]
        elif isinstance(sub, ast.Compare):
            for op in sub.ops:
                if type(op).__name__ in rules.ORDER_COMPARISONS:
                    return rules.ORDER_COMPARISONS[type(op).__name__]
        elif isinstance(sub, ast.Name):
            bound = env.get(sub.id)
            if isinstance(bound, Unknown) and bound.category == "not-a-simplification":
                return bound.reason
    return None


def _preorder(node):
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _preorder(child)


def _negative(test):
    """Whether the assert checks that two things are *not* equal."""
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return True
    return isinstance(test, ast.Compare) and any(
        isinstance(op, (ast.NotEq, ast.IsNot)) for op in test.ops)


def _describe(test):
    if isinstance(test, ast.BoolOp):
        return "an and/or of several checks"
    if isinstance(test, ast.Call):
        func = test.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "?")
        return f"a call of {name} (a helper or a check the generator does not follow)"
    return f"a bare {type(test).__name__} expression, not a comparison"


def split_call(operand):
    """``(receiver, call)``: an outermost SymPy call of the catalogue split off
    the operand, or ``(operand, "auto")``."""
    if isinstance(operand, ast.Call) and not operand.keywords:
        func = operand.func
        if isinstance(func, ast.Attribute):
            names = tuple(a.id if isinstance(a, ast.Name) else None for a in operand.args)
            key = (func.attr, names)
            if key in rules.CALL_METHODS:
                return func.value, rules.CALL_METHODS[key]
        if (isinstance(func, ast.Name) and func.id in rules.CALL_FUNCTIONS
                and len(operand.args) == 1):
            return operand.args[0], rules.CALL_FUNCTIONS[func.id]
    return operand, "auto"


def _as_expr(v):
    """A ``V`` whose expression is an nary expression (ints become literals)."""
    if isinstance(v.expr, bool) or isinstance(v.expr, tuple):
        raise NotTranslatable("an operand that is not a single expression")
    if isinstance(v.expr, int):
        return V(nr.NumberKind(v.expr), v.assume)
    return v


@dataclass
class Candidate:
    input: nr.Expr
    expected: nr.Expr
    call: str
    assume: dict
    operand: int


def candidates(test, translator, scope):
    """The candidate entries of an ``==``/``is`` comparison, or raise
    ``Classified``."""
    operands = [test.left] + list(test.comparators)
    split = [split_call(o) for o in operands]
    inputs = []
    try:
        for receiver, _ in split:
            inputs.append(_as_expr(translator.value(receiver)))
        try:
            value = eval(compile(ast.Expression(operands[-1]), "<test>", "eval"), scope)
        except Exception as error:  # noqa: BLE001 - any failure is a reason
            raise NotTranslatable(f"SymPy could not evaluate the right side here "
                                  f"({type(error).__name__})") from None
        try:
            value = sympy.sympify(value, strict=True)
        except (sympy.SympifyError, TypeError):
            raise NotTranslatable(f"the right side is a {type(value).__name__}, "
                                  f"not an expression") from None
        expected = _as_expr(from_sympy(value))
    except NotTranslatable as error:
        raise Classified("not-translatable", str(error)) from None
    labels = set()
    for v in inputs + [expected]:
        if isinstance(v.expr, Missing):
            labels |= v.expr.labels
    if labels:
        raise Classified("out-of-vocabulary", "needs " + ", ".join(sorted(labels)))
    found = []
    order = list(range(len(inputs) - 1))
    if all(normal(inputs[i].expr) == normal(expected.expr) for i in order):
        order = [len(inputs) - 1]  # the test wrote the simplified form first
    for i in order:
        v, call = inputs[i], split[i][1]
        if normal(v.expr) == normal(expected.expr):
            continue
        try:
            assume = merge(v.assume, expected.assume)
        except NotTranslatable as error:
            raise Classified("not-translatable", str(error)) from None
        assume = {name: facts for name, facts in assume.items() if facts}
        found.append(Candidate(v.expr, expected.expr, call, assume, i))
    if not found:
        raise Classified("not-a-simplification", "SymPy leaves it as written")
    return found


# ---- the checks of a candidate ---------------------------------------------


def sympy_call(c):
    """The SymPy call that turns the candidate's input into its expected
    value (``"auto"`` if the constructors already do), or raise
    ``Classified`` with what went wrong."""
    given, expected = to_sympy(c.input, c.assume), to_sympy(c.expected, c.assume)
    call = "auto" if given == expected else c.call
    try:
        made, again = run(call, given), run(call, expected)
    except Exception as error:  # noqa: BLE001
        raise Classified("not-translatable", f"SymPy's {call} fails on the nary form "
                                             f"({type(error).__name__})") from None
    if made != expected:
        raise Classified("not-translatable",
                         f"SymPy, given the nary form, does not give the test's value "
                         f"(call {call}): the test relies on how it builds the expression")
    if again != expected:
        raise Classified("not-translatable", f"SymPy's {call} changes the expected value")
    return call


def _value_free(e, point):
    """The innermost subexpression of ``e`` with no value at ``point`` whose
    arguments all have values, with those values; or None."""
    if numeric.evaluate(e, point) is not None:
        return None
    for a in e.args:
        inner = _value_free(a, point)
        if inner is not None:
            return inner
    return e, [numeric.evaluate(a, point) for a in e.args]


def _label(e, values):
    if e.head == nr.Pow:
        base, exponent = values
        if numeric._is_zero(base):
            if numeric._is_zero(exponent):
                return "Pow(0, 0)"
            return "Pow(0, w) with re(w) <= 0"
    if e.head == nr.log:
        return "log(0)"
    if e.head == nr.tan:
        return "tan(pole)"
    return f"{e.head!r}(...)"


def cause(input, expected, counterexamples):
    """The undecided class of an entry whose counterexamples all have one
    side without a value: at each point, the side without a value and its
    innermost subexpression with no value although its arguments have one,
    as ``"<side>: <label>"``; the class is the sorted set, joined by
    ``"; "``."""
    found = set()
    for point, a, b in counterexamples:
        side, e = ("input", input) if a is None else ("expected", expected)
        sub, values = _value_free(e, point)
        found.add(f"{side}: {_label(sub, values)}")
    return "; ".join(sorted(found))


def status_of(entry):
    """``(status, cause)`` from the numerical check: wrong values at some
    point -> rejected; otherwise, a point no precision decides
    (``numeric.Result.unsure``) -> undecided, class ``rules.UNSURE``;
    otherwise only definedness -> undecided, class from ``cause``."""
    result = numeric.check(entry.input, entry.expected, entry.when)
    if result.value_counterexamples:
        return "rejected", None
    if result.unsure:
        return "undecided", rules.UNSURE
    if result.counterexamples:
        found = cause(entry.input, entry.expected, result.counterexamples)
        if found not in rules.UNDECIDED_CLASSES:
            raise KeyError(f"{entry.name}: the undecided class {found!r} is not in "
                           "rules.UNDECIDED_CLASSES; add it there (with no decision)")
        return "undecided", found
    return "accepted", None


def tags_of(input, expected, call):
    """The tags of a generated entry, by the fixed rules of ``rules.TAG_RULES``."""
    tags = []
    if not numeric.symbols_of(input):
        tags.append("literal-arithmetic")
    if _has_rational_literal(input) or _has_rational_literal(expected):
        tags.append("rational-literals")
    if call in rules.EXPANSION_CALLS:
        tags.append("expansion")
    return tuple(tags)


def _has_rational_literal(e):
    if (e.head == nr.Pow and e.args[0].is_literal and e.args[1].is_literal
            and e.args[1].value < 0):
        return True
    return any(_has_rational_literal(a) for a in e.args)


# ---- walking a test file ---------------------------------------------------


@dataclass
class Generated:
    """What the generator found in one file."""
    stem: str
    path: str
    rows: list = field(default_factory=list)
    entries: list = field(default_factory=list)
    links: dict = field(default_factory=dict)
    symbols: dict = field(default_factory=dict)


def _bound_names(node):
    """The names a statement binds (assignment targets, loop variables,
    definitions, imports), anywhere inside it."""
    names = []
    for sub in _preorder(node):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
            names.append(sub.id)
        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(sub.name)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            names.extend((a.asname or a.name).split(".")[0] for a in sub.names)
    return names


class FileGenerator:
    def __init__(self, stem):
        self.stem = stem
        self.path, self.sha = rules.FILES[stem]
        self.module = importlib.import_module(module_name(self.path))
        data = Path(self.module.__file__).read_bytes()
        if git_blob_sha(data) != self.sha:
            raise RuntimeError(f"{self.module.__file__} is not the pinned file "
                               f"(blob {self.sha})")
        self.tree = ast.parse(data, filename=self.path)
        self.out = Generated(stem, self.path)
        self.by_key = {}
        self.positions = self._positions()
        from ..entries import HAND_WRITTEN
        self.hand_written = [e for e in HAND_WRITTEN if e.has_nary_form]

    def _positions(self):
        starts = {}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assert):
                starts.setdefault(node.lineno, []).append(node)
        positions = {}
        for line, nodes in starts.items():
            for i, node in enumerate(sorted(nodes, key=lambda n: n.col_offset)):
                positions[id(node)] = i
        return positions

    def source(self, function, node):
        return Source(self.path, function, node.lineno, node.end_lineno,
                      self.positions[id(node)])

    # -- walking ------------------------------------------------------------

    def run(self):
        for stmt in self.tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.function(stmt)
            else:
                for node in ast.walk(stmt):
                    if isinstance(node, ast.Assert):
                        self.row(Row(self.source("<module>", node), "not-translatable",
                                     "at module level"))
        self.out.rows.sort(key=lambda r: (r.source.line, r.source.position))
        return self.out

    def function(self, fn):
        self.name = fn.name
        self.scope = dict(vars(self.module))
        self.env = {}
        self.translator = Translator(vars(self.module), self.env)
        for stmt in fn.body:
            self.statement(stmt)

    def statement(self, stmt):
        if isinstance(stmt, ast.Assert):
            self.assertion(stmt)
        elif isinstance(stmt, ast.Assign):
            self.assign(stmt)
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
            exec(compile(ast.Module([stmt], []), self.path, "exec"), self.scope)
            for name in _bound_names(stmt):
                self.env.pop(name, None)
        elif isinstance(stmt, ast.Expr):
            pass  # a docstring or a bare call; nothing is bound
        else:
            reason = rules.CONTEXTS.get(type(stmt).__name__,
                                        f"inside a {type(stmt).__name__} statement")
            for node in ast.walk(stmt):
                if isinstance(node, ast.Assert):
                    self.row(Row(self.source(self.name, node), "not-translatable", reason))
            for name in _bound_names(stmt):
                self.scope.pop(name, None)
                if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)) and name == stmt.name:
                    self.env[name] = Helper(name)
                else:
                    self.env[name] = Unknown("not-translatable",
                                             f"uses {name}, bound {reason}")

    def assign(self, stmt):
        pairs = []
        for target in stmt.targets:
            if isinstance(target, ast.Tuple) and isinstance(stmt.value, ast.Tuple) \
                    and len(target.elts) == len(stmt.value.elts):
                pairs.extend(zip(target.elts, stmt.value.elts))
            else:
                pairs.append((target, stmt.value))
        for target, value in pairs:
            self.bind(target, value)

    def bind(self, target, value):
        names = _bound_names(target)
        try:
            assign = ast.copy_location(ast.Assign([target], value), target)
            exec(compile(ast.fix_missing_locations(ast.Module([assign], [])), self.path,
                         "exec"), self.scope)
        except Exception:  # noqa: BLE001 - the names are then unknown to SymPy
            for name in names:
                self.scope.pop(name, None)
        query = query_reason(value, self.env)
        if query:
            for name in names:
                self.env[name] = Unknown("not-a-simplification", f"uses {name}, from {query}")
            return
        try:
            v = self.translator.value(value)
            if isinstance(target, ast.Name):
                self.env[target.id] = v
                return
            if (isinstance(target, ast.Tuple) and isinstance(v.expr, tuple)
                    and len(v.expr) == len(target.elts)
                    and all(isinstance(t, ast.Name) for t in target.elts)):
                for t, item in zip(target.elts, v.expr):
                    self.env[t.id] = item
                return
            raise NotTranslatable("an assignment the generator does not unpack")
        except NotTranslatable as error:
            for name in names:
                self.env[name] = Unknown("not-translatable", f"uses {name}: {error}")

    # -- one assert ---------------------------------------------------------

    def assertion(self, stmt):
        source = self.source(self.name, stmt)
        try:
            entries = self.classify(stmt.test, source)
        except Classified as c:
            self.row(Row(source, c.category, c.reason))
        else:
            self.row(Row(source, "entry", "", entries))

    def classify(self, test, source):
        query = query_reason(test, self.env)
        if query:
            raise Classified("not-a-simplification", query)
        if _negative(test):
            raise Classified("non-rewrite", rules.NON_REWRITE)
        if not isinstance(test, ast.Compare):
            raise Classified("not-translatable", _describe(test))
        for op in test.ops:
            if not isinstance(op, (ast.Eq, ast.Is)):
                raise Classified("not-translatable", f"a comparison with {type(op).__name__}")
        found = candidates(test, self.translator, self.scope)
        names, failures = [], []
        for c in found:
            try:
                names.append(self.add(c, source))
            except Classified as failure:
                failures.append(failure)
        if not names:
            raise failures[0]
        return tuple(dict.fromkeys(names))

    def add(self, c, source):
        """Add the candidate as an entry (or a source of an existing or a
        hand-written one); return the entry's name."""
        call = sympy_call(c)
        for h in self.hand_written:
            if (normal(h.input) == normal(c.input) and normal(h.expected) == normal(c.expected)
                    and h.assume == c.assume):
                sources = self.out.links.setdefault(h.name, [])
                if source not in sources:
                    sources.append(source)
                return h.name
        key = (repr(c.input), repr(c.expected), call, repr(sorted(c.assume.items())))
        if key in self.by_key:
            i = self.by_key[key]
            e = self.out.entries[i]
            if source not in e.sources:
                self.out.entries[i] = replace(e, sources=e.sources + (source,))
            return e.name
        name = f"{self.stem}_l{source.line}"
        if source.position:
            name += f"p{source.position}"
        if c.operand:
            name += f"_{c.operand}"
        assume = {k: dict(sorted(v.items())) for k, v in sorted(c.assume.items())}
        probe = generated(name, c.input, c.expected, status="accepted", sympy=call,
                          area=rules.AREAS[self.stem], sources=(source,), assume=assume)
        status, found = status_of(probe)
        kind = None
        if status == "rejected":
            kind = "wrong-value"
        elif status == "undecided":
            kind = rules.UNDECIDED_CLASSES[found]["kind"]
        e = generated(name, c.input, c.expected, status=status, sympy=call,
                      area=rules.AREAS[self.stem], sources=(source,), assume=assume,
                      tags=tags_of(c.input, c.expected, call), kind=kind, cause=found)
        self.by_key[key] = len(self.out.entries)
        self.out.entries.append(e)
        return name

    def row(self, row):
        self.out.rows.append(row)


def generate(stem):
    """The ledger and entries of the test file with stem ``stem``."""
    return FileGenerator(stem).run()


# ---- writing ---------------------------------------------------------------

_NAMESPACE_NAMES = ("Add", "Mul", "Pow", "E", "I", "pi", "exp", "log", "sin", "cos", "tan")


def _namespace(symbols):
    ns = {name: getattr(nr, name) for name in _NAMESPACE_NAMES}
    for s in symbols:
        if s in ns:
            raise ValueError(f"a symbol named {s} would shadow nary's {s}")
        ns[s] = nr.NumberKind(s)
    return ns


def _expr(e, ns):
    text = repr(e)
    back = eval(text, dict(ns))
    if (nr.NumberKind(back) if isinstance(back, int) else back) != e:
        raise ValueError(f"{text} does not read back as the same expression")
    return text


def _source(s):
    position = f", {s.position}" if s.position else ""
    return f"_s({s.function!r}, {s.line}, {s.end_line}{position})"


def _sources(sources):
    return "(" + "".join(_source(s) + ", " for s in sources).rstrip(" ") + ")"


def render_py(g):
    symbols = sorted({name for e in g.entries for name, _ in numeric.symbols_of(e.input,
                                                                                e.expected)})
    ns = _namespace(symbols)
    lines = [
        f'"""GENERATED by `python -m catalogue.from_tests` from {g.path}',
        f"of SymPy at {SYMPY_COMMIT}",
        "and the tables of catalogue/from_tests/rules.py. Do not edit: change rules.py",
        "(or the generator) and run",
        "",
        "    .venv/bin/python -m catalogue.from_tests",
        "",
        "LEDGER has one Row per assert statement of the file; ENTRIES are the",
        "generated catalogue entries; LINKS gives the sources of hand-written",
        'entries that the file also asserts. See power.md for the same as a table."""',
        "",
        "import nary as nr",
        f"from nary import {', '.join(_NAMESPACE_NAMES)}  # noqa: F401",
        "",
        "from ..entry import Source, generated",
        "from .ledger import Row",
        "",
    ]
    lines += [f'{s} = nr.NumberKind("{s}")' for s in symbols]
    lines += [
        "",
        "",
        "def _s(function, line, end_line, position=0):",
        f"    return Source({g.path!r}, function, line, end_line, position)",
        "",
        "",
        "LEDGER = [",
    ]
    for r in g.rows:
        args = [_source(r.source), repr(r.category)]
        if r.reason:
            args.append(repr(r.reason))
        if r.entries:
            if not r.reason:
                args.append("''")
            args.append(repr(tuple(r.entries)))
        lines.append(f"    Row({', '.join(args)}),")
    lines += ["]", "", "ENTRIES = ["]
    for e in g.entries:
        args = [repr(e.name), _expr(e.input, ns), _expr(e.expected, ns),
                f"status={e.status!r}", f"sympy={e.sympy!r}", f"area={e.area!r}",
                f"sources={_sources(e.sources)}"]
        if e.assume:
            args.append(f"assume={e.assume!r}")
        if e.tags:
            args.append(f"tags={e.tags!r}")
        if e.kind:
            args.append(f"kind={e.kind!r}")
        if e.cause:
            args.append(f"cause={e.cause!r}")
        lines.append("    generated(" + ",\n              ".join(args) + "),")
    lines += ["]", "", "LINKS = {"]
    for name in sorted(g.links):
        lines.append(f"    {name!r}: {_sources(g.links[name])},")
    lines += ["}", ""]
    return "\n".join(lines)


def _md_escape(text):
    return text.replace("|", "\\|")


def render_md(g):
    statuses = {e.name: e.status for e in g.entries}
    from ..entries import HAND_WRITTEN
    hand = {e.name: e.status for e in HAND_WRITTEN}
    categories = Counter(r.category for r in g.rows)
    lines = [
        f"<!-- GENERATED by `python -m catalogue.from_tests`; do not edit. -->",
        f"# Catalogue ledger: `{g.path}`",
        "",
        f"SymPy commit [{SYMPY_COMMIT[:10]}](https://github.com/sympy/sympy/tree/{SYMPY_COMMIT}) "
        f"(release 1.14.0). One row per assert statement: {len(g.rows)} rows.",
        "",
        "| category | asserts | meaning |",
        "|---|---|---|",
    ]
    for category, meaning in rules.CATEGORIES.items():
        lines.append(f"| {category} | {categories[category]} | {meaning} |")
    by_status = Counter(e.status for e in g.entries)
    lines += [
        "",
        f"Generated entries: {len(g.entries)} ("
        + ", ".join(f"{s} {by_status[s]}" for s in ("accepted", "rejected", "undecided"))
        + f"); hand-written entries linked: {len(g.links)}"
        + (f" ({', '.join(sorted(g.links))})" if g.links else "") + ".",
    ]
    classes = Counter(e.cause for e in g.entries if e.cause)
    if classes:
        lines += ["", "Undecided classes:", ""]
        for name, count in sorted(classes.items()):
            lines.append(f"- `{name}`: {count}. {rules.UNDECIDED_CLASSES[name]['description']}")
    lines += ["", "Reasons, by category:", ""]
    for category in rules.CATEGORIES:
        if category == "entry":
            continue
        reasons = Counter(r.reason for r in g.rows if r.category == category)
        if reasons:
            lines.append(f"- {category}:")
            for reason, count in sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0])):
                lines.append(f"  - {count}: {_md_escape(reason)}")
    lines += ["", "| assert | category | entries or reason |", "|---|---|---|"]
    for r in g.rows:
        s = r.source
        label = f"{s.function} L{s.line}" + (f".{s.position}" if s.position else "")
        if r.entries:
            what = ", ".join(f"`{n}` ({statuses.get(n) or 'hand-written, ' + hand[n]})"
                             for n in r.entries)
        else:
            what = _md_escape(r.reason)
        lines.append(f"| [{label}]({s.url}) | {r.category} | {what} |")
    return "\n".join(lines) + "\n"


def render(stem="power"):
    """``{path: text}`` of the files the generator writes for ``stem``."""
    g = generate(stem)
    return {HERE / f"{stem}.py": render_py(g), HERE / f"{stem}.md": render_md(g)}


def write():
    for stem in rules.FILES:
        for path, text in render(stem).items():
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path}")
