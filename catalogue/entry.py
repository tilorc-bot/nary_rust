"""What a catalogue entry is.

An entry says: ``input`` should simplify to ``expected``, where ``when``
holds. It is written with nary's own expressions, in the shape of
``nary.rules.rule(pattern, replacement, when=)``, so that
``Entry.as_rule()`` is a ``Rule`` and the same entry can be run through
``nary.rewriting.rewrite`` and printed to Lean.

The catalogue is one list, ``catalogue.entries.ENTRIES``, and every entry
has a ``status``:

- ``"accepted"``: a desired simplification. SymPy makes it, the numerical
  check finds no counterexample, it is run through the engine and stated in
  Lean.
- ``"rejected"``: something SymPy does that is wrong: the numerical check
  finds a point where both sides have a value and the values differ. Kept
  so that the test fails if it ever stops being wrong.
- ``"undecided"``: SymPy and nary's semantics (issue #2) do not line up, and
  Tilo has not decided what the catalogue should do. The entry records the
  options and the question.

Symbols in an entry stand for numbers (or propositions) that have a value,
as they do when the entry is given to ``rewrite``; unlike in a rule, they do
not range over "no value". ``catalogue.lean`` states an entry that way.

``when`` is not written by hand: it is derived from ``assume``, the SymPy
assumptions under which SymPy makes the simplification, through the fixed
table ``ASSUMPTIONS``. So the condition the entry is checked under is the
one SymPy was given, translated, and nothing else.

Fields of every entry:

- ``name``: an identifier, also the name of the Lean statement.
- ``status``: one of ``STATUSES``.
- ``input``, ``expected``: nary expressions of the same kind. For a
  rejected or undecided entry, the claim SymPy's result makes; both are
  ``None`` when it cannot be written in nary (then only the SymPy text is
  recorded).
- ``area``: what it is about, from ``AREAS``; only for grouping.
- ``tags``: the machinery the entry seems to need, from ``TAGS``.
- ``assume``: SymPy assumptions by symbol name, such as
  ``{"x": {"positive": True}}``.
- ``needs``: open pull requests that would provide part of that machinery,
  such as ``("#27",)``.
- ``note``: anything else worth saying.

For an accepted entry:

- ``sympy``: how SymPy gets it, a key of ``catalogue.sympy_check.CALLS``.
  ``"auto"`` means SymPy's constructors already do it.

For a rejected or undecided entry (what ``catalogue/mismatches.py`` used
to hold):

- ``kind``: why it is not accepted, from ``KINDS``.
- ``sympy_source``: a SymPy expression in Python syntax, evaluated with
  everything from ``sympy`` and the symbols ``x, y, a, b`` (no
  assumptions), ``n`` (``integer=True``), ``r`` (``real=True``), ``p, q``.
- ``sympy_gives``: its ``repr``, or, if it raises, the name of the
  exception. Tested against the pinned SymPy.
- ``semantics``: what nary's semantics say about it.
- ``options``: the choices, as text.
- ``question``: the question for Tilo.
- ``numeric``: what ``catalogue.numeric.check`` finds on ``input ->
  expected`` (always without a condition), when they are given:

  - ``"value"``: a point where both sides have a value and the values
    differ. SymPy's result is wrong, whatever one thinks of definedness.
    Exactly the rejected entries.
  - ``"definedness"``: points where one side has a value and the other has
    none, and no point where both have different values. SymPy's result is
    right where both sides have a value; nary's semantics reject it as a
    rewrite.
  - ``"none"``: no counterexample among the points tried. Used where the
    difference is one the numerical check cannot see; ``semantics`` says
    why.

- ``no_value``: an nary expression that must have no value under
  ``catalogue.numeric``: what SymPy gives a value to (or refuses).
"""

from dataclasses import dataclass, field

import nary as nr
from nary.logic import And
from nary.rules import rule

__all__ = ["AREAS", "ASSUMPTIONS", "Entry", "KINDS", "NO_CONDITION", "NUMERIC", "STATUSES",
           "Source", "TAGS", "entry", "generated", "rejected", "undecided"]

STATUSES = ("accepted", "rejected", "undecided")

# Why an entry is not accepted. ``condition``: SymPy's result holds only under
# a condition SymPy does not ask for. ``off-domain``: SymPy gives a value, or an
# error, where nary has no value. ``vocabulary``: nary has no way to write the
# input, output or assumption. ``comparison``: what "reaches expected" should
# mean. ``representation``. ``assumptions``: translating SymPy's assumptions.
# ``wrong-value``: SymPy's result is wrong (the rejected entries).
KINDS = ("condition", "off-domain", "vocabulary", "comparison", "representation",
         "assumptions", "wrong-value")

NUMERIC = ("value", "definedness", "none")

# The machinery an entry seems to need. An entry usually has several.
TAGS = {
    "rule": "a plain rewrite rule (pattern -> replacement, maybe with when=) of the kind "
            "main already has; no new engine feature",
    "literal-arithmetic": "arithmetic on integer literals (open PR #27)",
    "rational-literals": "rational numbers; main has integer literals only, so 1/2 is "
                         "written Pow(2, -1)",
    "normal-form": "collecting like terms, or a canonical form of sums and products, "
                   "beyond one rule application",
    "matching": "more matching than main's engine does (a variable matching several "
                "arguments, or a partial match of Add/Mul below the top)",
    "expansion": "distributing products and powers over sums",
    "strategy": "a choice between equivalent forms (factor, cancel, trigsimp); no "
                "obvious terminating rule set",
    "special-values": "a function at a particular point, such as sin(pi) = 0",
    "assumptions": "the condition must be derived from assumptions, not just looked up",
    "decide-literals": "a condition on literals must be decided, such as Ne(2, 0) or "
                       "that an exponent is an integer",
    "definedness": "an erased subexpression must be shown to have a value",
    "lambda": "calling a lambda (substitution)",
    "calculus": "rules for Derivative",
}

AREAS = ("arithmetic", "powers", "exp-log", "trig", "complex", "logic", "relational",
         "calculus", "lambda", "conventions")


# SymPy assumption -> the nary condition on the symbol. SymPy's
# ``nonzero=True`` means real and not zero; ``zero=False`` is the complex
# "not zero", which is what Ne(s, 0) says.
ASSUMPTIONS = {
    ("zero", False): lambda s: nr.Ne(s, 0),
    ("positive", True): lambda s: nr.Gt(s, 0),
    ("negative", True): lambda s: nr.Lt(s, 0),
    ("nonnegative", True): lambda s: nr.Ge(s, 0),
    ("nonpositive", True): lambda s: nr.Le(s, 0),
    ("real", True): lambda s: nr.Eq(nr.re(s), s),
}

# SymPy assumptions that every nary number symbol in an entry already has
# (it stands for a complex number): kept in ``assume``, so that SymPy sees
# them, with no nary condition.
NO_CONDITION = {("complex", True)}


@dataclass(frozen=True)
class Source:
    """An assert statement of a SymPy test file that an entry comes from:
    ``file`` is the path in the SymPy repository, ``line`` to ``end_line``
    the lines of the assert, ``position`` its index among the asserts that
    start on that line."""
    file: str
    function: str
    line: int
    end_line: int
    position: int = 0

    @property
    def id(self):
        """The ledger id: file, test function, line (and position)."""
        suffix = f".{self.position}" if self.position else ""
        return f"{self.file}::{self.function}::L{self.line}{suffix}"

    @property
    def url(self):
        """A permalink to the assert at the pinned SymPy commit."""
        from .sympy_check import SYMPY_COMMIT
        lines = f"L{self.line}" if self.end_line == self.line else f"L{self.line}-L{self.end_line}"
        return f"https://github.com/sympy/sympy/blob/{SYMPY_COMMIT}/{self.file}#{lines}"


@dataclass(frozen=True)
class Entry:
    name: str
    status: str
    input: nr.Expr
    expected: nr.Expr
    area: str
    tags: tuple = ()
    assume: dict = field(default_factory=dict)
    needs: tuple = ()
    note: str = ""
    sympy: str = None
    kind: str = None
    sympy_source: str = None
    sympy_gives: str = None
    semantics: str = ""
    options: tuple = ()
    question: str = ""
    numeric: str = None
    no_value: object = None
    sources: tuple = ()
    generated: bool = False
    cause: str = None

    @property
    def has_nary_form(self):
        """Whether ``input`` and ``expected`` are given."""
        return self.input is not None

    @property
    def conditions(self):
        """The conditions of ``when``, one per assumption, as a tuple."""
        found = []
        symbols = {}
        for e in (self.input, self.expected):
            for s in _symbols(e) if e is not None else ():
                symbols.setdefault(s.name, s)
        for name, facts in self.assume.items():
            for fact in facts.items():
                if fact in NO_CONDITION:
                    continue
                if fact not in ASSUMPTIONS:
                    raise ValueError(f"{self.name}: no nary condition for the SymPy "
                                     f"assumption {fact} on {name}")
                found.append(ASSUMPTIONS[fact](symbols[name]))
        return tuple(found)

    @property
    def when(self):
        """The condition of the entry, a ``BoolKind`` expression or ``None``."""
        conditions = self.conditions
        if not conditions:
            return None
        return conditions[0] if len(conditions) == 1 else And(*conditions)

    def as_rule(self):
        """The entry as a ``Rule``, ``rule(input, expected, when=when)``."""
        return rule(self.input, self.expected, when=self.when, name=self.name)


def _symbols(e):
    if e.is_symbol:
        yield e
    elif e.head is not None:
        yield from _symbols(e.head)
        for a in e.args:
            yield from _symbols(a)


def _check_tags_area(name, tags, area):
    unknown = set(tags) - set(TAGS)
    if unknown:
        raise ValueError(f"{name}: unknown tags {sorted(unknown)}")
    if area not in AREAS:
        raise ValueError(f"{name}: unknown area {area!r}")


def _literal(e):
    return nr.NumberKind(e) if isinstance(e, int) else e


def entry(name, input, expected, *, sympy, tags, area, assume=None, needs=(), note=""):
    """Make an accepted ``Entry``, converting a Python int ``expected`` to a
    literal."""
    _check_tags_area(name, tags, area)
    return Entry(name, "accepted", input, _literal(expected), area, tuple(tags),
                 dict(assume or {}), tuple(needs), note, sympy=sympy)


def _not_accepted(status, name, kind, input, expected, *, area, sympy_source, sympy_gives,
                  semantics, options, question, numeric, no_value, tags, note):
    _check_tags_area(name, tags, area)
    if kind not in KINDS:
        raise ValueError(f"{name}: unknown kind {kind!r}")
    if (input is None) != (expected is None):
        raise ValueError(f"{name}: give both input and expected, or neither")
    if (numeric is None) != (input is None) or numeric not in NUMERIC + (None,):
        raise ValueError(f"{name}: numeric must be one of {NUMERIC} exactly when there is "
                         "an nary form")
    return Entry(name, status, input, _literal(expected), area, tuple(tags), {}, (), note,
                 kind=kind, sympy_source=sympy_source, sympy_gives=sympy_gives,
                 semantics=semantics, options=tuple(options), question=question,
                 numeric=numeric, no_value=no_value)


def rejected(name, input, expected, *, area, sympy_source, sympy_gives, semantics, options,
             question, tags=(), note=""):
    """Make a rejected ``Entry``: SymPy turns ``input`` into ``expected``
    (``sympy_source`` gives ``sympy_gives``), and the numerical check finds
    wrong values."""
    return _not_accepted("rejected", name, "wrong-value", input, expected, area=area,
                         sympy_source=sympy_source, sympy_gives=sympy_gives,
                         semantics=semantics, options=options, question=question,
                         numeric="value", no_value=None, tags=tags, note=note)


def undecided(name, kind, input=None, expected=None, *, area, sympy_source, sympy_gives,
              semantics, options, question, numeric=None, no_value=None, tags=(), note=""):
    """Make an undecided ``Entry``: a case where SymPy and nary do not line
    up, waiting for Tilo."""
    if kind == "wrong-value":
        raise ValueError(f"{name}: a wrong value is rejected, not undecided")
    return _not_accepted("undecided", name, kind, input, expected, area=area,
                         sympy_source=sympy_source, sympy_gives=sympy_gives,
                         semantics=semantics, options=options, question=question,
                         numeric=numeric, no_value=no_value, tags=tags, note=note)


def generated(name, input, expected, *, status, sympy, area, sources, assume=None, tags=(),
              kind=None, cause=None):
    """Make an ``Entry`` generated from SymPy's tests by
    ``catalogue.from_tests``. ``sympy`` is the SymPy call for all statuses
    (the generator checked that SymPy, so called, gives ``expected``). A
    rejected entry has ``numeric="value"``; an undecided one has
    ``numeric="definedness"`` and ``cause``, its class in
    ``catalogue.from_tests.rules.UNDECIDED_CLASSES``."""
    _check_tags_area(name, tags, area)
    if status not in STATUSES:
        raise ValueError(f"{name}: unknown status {status!r}")
    numeric = {"accepted": None, "rejected": "value", "undecided": "definedness"}[status]
    if (cause is not None) != (status == "undecided"):
        raise ValueError(f"{name}: give a cause exactly for an undecided entry")
    return Entry(name, status, input, _literal(expected), area, tuple(tags), dict(assume or {}),
                 sympy=sympy, kind=kind, numeric=numeric, sources=tuple(sources),
                 generated=True, cause=cause)
