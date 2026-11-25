"""What a catalogue entry is.

An entry says: ``input`` should simplify to ``expected``, where ``when``
holds. It is written with nary's own expressions, in the shape of
``nary.rules.rule(pattern, replacement, when=)``, so that
``Entry.as_rule()`` is a ``Rule`` and the same entry can be run through
``nary.rewriting.rewrite`` and printed to Lean.

Symbols in an entry stand for numbers (or propositions) that have a value,
as they do when the entry is given to ``rewrite``; unlike in a rule, they do
not range over "no value". ``catalogue.lean`` states an entry that way.

``when`` is not written by hand: it is derived from ``assume``, the SymPy
assumptions under which SymPy makes the simplification, through the fixed
table ``ASSUMPTIONS``. So the condition the entry is checked under is the
one SymPy was given, translated, and nothing else.

Fields:

- ``name``: an identifier, also the name of the Lean statement.
- ``input``, ``expected``: nary expressions of the same kind.
- ``sympy``: how SymPy gets it, a key of ``catalogue.sympy_check.CALLS``.
  ``"auto"`` means SymPy's constructors already do it.
- ``assume``: SymPy assumptions by symbol name, such as
  ``{"x": {"positive": True}}``.
- ``tags``: the machinery the entry seems to need, from ``TAGS``.
- ``area``: what it is about, from ``AREAS``; only for grouping.
- ``needs``: open pull requests that would provide part of that machinery,
  such as ``("#27",)``.
- ``note``: anything else worth saying.
"""

from dataclasses import dataclass, field

import nary as nr
from nary.logic import And
from nary.rules import rule

__all__ = ["AREAS", "ASSUMPTIONS", "Entry", "TAGS", "entry"]

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
         "calculus", "lambda")


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


@dataclass(frozen=True)
class Entry:
    name: str
    input: nr.Expr
    expected: nr.Expr
    sympy: str
    tags: tuple
    area: str
    assume: dict = field(default_factory=dict)
    needs: tuple = ()
    note: str = ""

    @property
    def conditions(self):
        """The conditions of ``when``, one per assumption, as a tuple."""
        found = []
        symbols = {}
        for e in (self.input, self.expected):
            for s in _symbols(e):
                symbols.setdefault(s.name, s)
        for name, facts in self.assume.items():
            for fact in facts.items():
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


def entry(name, input, expected, *, sympy, tags, area, assume=None, needs=(), note=""):
    """Make an ``Entry``, converting a Python int ``expected`` to a literal."""
    if isinstance(expected, int):
        expected = nr.NumberKind(expected)
    unknown = set(tags) - set(TAGS)
    if unknown:
        raise ValueError(f"{name}: unknown tags {sorted(unknown)}")
    if area not in AREAS:
        raise ValueError(f"{name}: unknown area {area!r}")
    return Entry(name, input, expected, sympy, tuple(tags), area, dict(assume or {}),
                 tuple(needs), note)
