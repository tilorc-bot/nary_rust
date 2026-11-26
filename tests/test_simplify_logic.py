import pytest
from nary import (
    BoolKind,
    E,
    Eq,
    Ge,
    Gt,
    I,
    Le,
    Lt,
    Mul,
    Ne,
    NumberKind,
    Pow,
    exp,
    log,
    pi,
    re,
    tan,
)
from nary.logic import And, Not, Or, false, true
from nary.rewriting import implications
from nary.rules import rule
from nary.simplify import simplify
from nary.strategies import apply
from test_soundness import check

x, y = NumberKind("x"), NumberKind("y")
p, q = BoolKind("p"), BoolKind("q")
positive, negative, real = [Gt(x, 0), Gt(y, 0)], [Lt(x, 0), Lt(y, 0)], [Eq(re(x), x)]
third = Pow(3, -1)

CASES = [
    (Or(p, Lt(x, y), true), [], true),
    (And(Lt(x, y), false, q), [], false),
    (Not(And(p, p)), [], Not(p)),
    (Not(Or(p, q)), [], And(Not(p), Not(q))),
    (Not(Lt(x, y)), [], Ge(x, y)),
    (And(p, Not(p)), [], false),
    (Or(p, And(p, q)), [], p),
    (Ge(log(8), pi + 9), [], false),
    (Lt(Pow(27, -1), tan(2 * pi * third)), [], false),
    (Eq(NumberKind(2), 3), [], false),
    (Ne(E, I), [], true),
    (Eq(x, x + 1), [], false),
    (Lt(x, x + 1), [], Lt(x, 1 + x)),
    (Lt(x, x + 1), real, true),
    (Eq(exp(x), 0), [], false),
    (Gt(x, -3), positive, true),
    (Ne(x, 0), positive, true),
    (Eq(re(x), x), positive, true),
    (Lt(x, 0), positive, false),
    (Ge(x**2, 0), real, true),
    (Gt(exp(x), 0), real, true),
    (Lt(Mul(-1, third, x), 0), negative, false),
    (Le(Mul(-3, x), Mul(2, y)), positive, true),
    (Gt(0, Pow(y, x)), positive, false),
]


@pytest.mark.parametrize(("e", "known", "expected"), CASES, ids=repr)
def test_simplify_logic(e, known, expected):
    assert simplify(e, known) == expected


STRATEGY_CASES = [
    ("to_nnf", Not(And(p, q, Lt(x, 1))), Or(Not(p), Not(q), Ge(x, 1))),
    ("to_nnf", And(p, Not(p)), false),
    ("simplify_logic", Or(p, And(p, q)), p),
    ("simplify_logic", Not(Or(p, q)), And(Not(p), Not(q))),
]


@pytest.mark.parametrize(("name", "e", "expected"), STRATEGY_CASES, ids=repr)
def test_logic_strategies(name, e, expected):
    assert apply(name, e) == expected


@pytest.mark.parametrize(("premise", "conclusion"), implications, ids=repr)
def test_implication_is_sound(premise, conclusion):
    held, counterexample = check(rule(conclusion, true, when=premise))
    assert counterexample is None and held > 0, counterexample
