"""satsimp's rows as nary rules, from tables.py; a row is strict when its left side has a value wherever the condition and the right side do.

    >>> trigsimp_tables()["normalize"]
    [Row(Rule(tan(u), Mul(Pow(cos(u), -1), sin(u))), 'rule', strict=True)]
    >>> sum(len(rows) for parts in refine_tables().values() for rows in parts), len(trigsimp_tables())
    (21, 5)
"""

from functools import cache
from typing import NamedTuple

from nary.logic import And, true
from nary.rules import rule

from . import tables
from .prove import definedness, prover

__all__ = ["Row", "refine_tables", "strict", "trigsimp_tables"]


class Row(NamedTuple):
    rule: object
    kind: str
    strict: bool
    opaque: tuple = ()

    def __repr__(self):
        return f"Row({self.rule!r}, {self.kind!r}, strict={self.strict})"


def strict(r):
    left, right = definedness(r.pattern), definedness(r.replacement)
    if left is None or right is None:
        return False
    return prover(right if r.condition is None else And(r.condition, right))(left)


def _rows(kind, opaque, rows):
    rules = [rule(lhs, rhs, when=None if condition == true else condition) for lhs, rhs, condition in rows]
    return [Row(r, kind, strict(r), opaque) for r in rules]


@cache
def refine_tables():
    return {head: [_rows(*part) for part in parts] for head, parts in tables.REFINE.items()}


@cache
def trigsimp_tables():
    return {name: _rows(*part) for name, part in tables.TRIGSIMP.items()}
