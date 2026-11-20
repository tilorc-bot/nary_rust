"""Printing expressions as Lean terms and rules as Lean statements, with
nary.lean. Lean itself is not needed: lean/check_printer.py checks printed
terms with Lean by hand, and `lake build` in lean/ checks the rules."""

import doctest
import importlib.util
from pathlib import Path

import nary as nr
import nary.lean
import pytest
from nary.arithmetic_rules import rules
from nary.calculus import Derivative, Integral, NumberFunction
from nary.lean import to_lean, to_lean_example, to_lean_rule
from nary.logic import And, Not, true
from nary.matrices import Matrix, Trace
from nary.rules import rule

x, y = nr.NumberKind("x"), nr.NumberKind("y")
p = nr.BoolKind("p")
f = NumberFunction("f")


def test_docstring_examples():
    result = doctest.testmod(nary.lean)
    assert result.attempted > 0
    assert result.failed == 0


def test_to_lean():
    assert to_lean(nr.Pow(x, 2) * nr.pi) == "Nary.Mul [Nary.Pow (some x) (Nary.lit 2), Nary.pi]"
    assert to_lean(And(p, Not(x < 0), true)) == (
        "Nary.And [some p, Nary.Not (Nary.Lt (some x) (Nary.lit 0)), Nary.true]"
    )
    assert to_lean(Derivative(nr.Lambda(x, nr.sin(x)))(f(y))) == (
        "Nary.apply (Nary.Derivative (fun x => Nary.sin (some x))) (Nary.apply f (some y))"
    )
    assert to_lean(nr.NumberKind("I") + nr.NumberKind("fun")) == "Nary.Add [some I, some «fun»]"
    assert to_lean_example(f(x) * y + nr.sin(x)) == (
        "noncomputable example (x y : ℂ) (f : ℂ → Nary.Number) : Nary.Number := "
        "Nary.Add [Nary.Mul [Nary.apply f (some x), some y], Nary.sin (some x)]"
    )
    # The variable of a lambda is not free.
    assert to_lean_example(nr.Lambda(x, x * y)) == (
        "noncomputable example (y : ℂ) : ℂ → Nary.Number := fun x => Nary.Mul [some x, some y]"
    )


def test_refused():
    with pytest.raises(ValueError, match="^Integral has no Lean definition"):
        to_lean(Integral(nr.sin, 0, x))
    with pytest.raises(ValueError, match="^Trace has no Lean definition"):
        to_lean(Trace(Matrix("A")) + 1)
    # A function named sin that is not nary's sin.
    other_sin = nr.declare_function("sin", nr.NumberKind, returns=nr.NumberKind, domain=true)
    with pytest.raises(ValueError, match="^sin has no Lean definition"):
        to_lean(other_sin(x))
    with pytest.raises(ValueError, match="only a Lambda of one NumberKind variable"):
        to_lean(nr.Lambda((x, y), x * y))
    with pytest.raises(ValueError, match="two free symbols are named x"):
        to_lean_example(And(nr.BoolKind("x"), x < 1))
    with pytest.raises(ValueError, match="a symbol named some cannot be written in Lean"):
        to_lean(nr.NumberKind("some"))


def test_to_lean_rule():
    by_name = {r.name: r for r in rules}
    assert to_lean_rule(by_name["add_zero"]) == (
        "abbrev add_zero : Prop :=\n  ∀ (a : Nary.Number), Nary.Add [a, Nary.lit 0] = a"
    )
    assert to_lean_rule(by_name["mul_zero"]) == (
        "abbrev mul_zero : Prop :=\n"
        "  ∀ (a : Nary.Number), a ≠ none → Nary.Mul [a, Nary.lit 0] = Nary.lit 0"
    )
    assert to_lean_rule(by_name["exp_log"]) == (
        "abbrev exp_log : Prop :=\n"
        "  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → Nary.exp (Nary.log a) = a"
    )
    assert to_lean_rule(by_name["collect"]) == (
        "abbrev collect : Prop :=\n  ∀ (m n : ℤ) (a : Nary.Number), "
        "Nary.Add [Nary.Mul [Nary.lit m, a], Nary.Mul [Nary.lit n, a]] "
        "= Nary.Mul [Nary.lit (m + n), a]"
    )
    # A function variable is a function, which always has a value, so the
    # wrong rule f(a) * 0 -> 0 prints as a false statement.
    assert to_lean_rule(rule(f(x) * 0, 0, name="wrong")) == (
        "abbrev wrong : Prop :=\n  ∀ (x : Nary.Number) (f : Nary.NumberFunction), "
        "x ≠ none → Nary.Mul [Nary.apply f x, Nary.lit 0] = Nary.lit 0"
    )


def test_to_lean_rule_refused():
    with pytest.raises(ValueError, match="has no name"):
        to_lean_rule(rule(x + 0, x))
    with pytest.raises(ValueError, match="the name must be a plain identifier"):
        to_lean_rule(rule(x + 0, x, name="add zero"))


def test_generated_lean_file_is_current():
    script = Path(__file__).resolve().parents[1] / "lean" / "generate_rules.py"
    spec = importlib.util.spec_from_file_location("generate_rules", script)
    generate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generate)
    assert generate.PATH.read_text(encoding="utf-8") == generate.render(), (
        "lean/Nary/ArithmeticRules/Statements.lean is out of date: run "
        ".venv/bin/python lean/generate_rules.py, then prove any new statement"
    )
