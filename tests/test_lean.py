import importlib.util
from pathlib import Path

import nary as nr
import pytest
from nary.arithmetic_rules import rules
from nary.calculus import Derivative, Integral, NumberFunction
from nary.lean import to_lean, to_lean_example, to_lean_facts, to_lean_rule
from nary.logic import And, Not, true
from nary.matrices import Matrix, Trace
from nary.rules import rule

x, y = nr.NumberKind("x"), nr.NumberKind("y")
p = nr.BoolKind("p")
f = NumberFunction("f")


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
    assert to_lean_example(nr.Lambda(x, x * y)) == (
        "noncomputable example (y : ℂ) : ℂ → Nary.Number := fun x => Nary.Mul [some x, some y]"
    )


def test_refused():
    with pytest.raises(ValueError, match="^Integral has no Lean definition"):
        to_lean(Integral(nr.sin, 0, x))
    with pytest.raises(ValueError, match="^Trace has no Lean definition"):
        to_lean(Trace(Matrix("A")) + 1)
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
    assert to_lean_rule(by_name["add_identity"]) == (
        "abbrev add_identity : Prop :=\n  ∀ (a : Nary.Number), Nary.Add [a, Nary.lit 0] = a"
    )
    assert to_lean_rule(by_name["mul_absorbing"]) == (
        "abbrev mul_absorbing : Prop :=\n"
        "  ∀ (a : Nary.Number), a ≠ none → Nary.Mul [a, Nary.lit 0] = Nary.lit 0"
    )
    assert to_lean_rule(by_name["mul_inverse"]) == (
        "abbrev mul_inverse : Prop :=\n"
        "  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → a ≠ none → "
        "Nary.Mul [a, Nary.Pow a (Nary.lit (-1))] = Nary.lit 1"
    )
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


LEAN = Path(__file__).resolve().parents[1] / "lean"


def test_names_that_are_quoted_or_refused():
    assert to_lean(nr.NumberKind("θ")) == "some «θ»"
    for name in ("", "none", "Nary", "a»"):
        with pytest.raises(ValueError):
            to_lean(nr.NumberKind(name))
    with pytest.raises(ValueError):
        to_lean(nr.Lambda(x, NumberFunction("x")(y)))
    with pytest.raises(ValueError):
        to_lean_rule(rule(x + 0, x, name="fun"))


def test_facts_are_refused_for_a_function_without_laws():
    for function in (nr.Pow, Integral):
        with pytest.raises(ValueError):
            to_lean_facts(function)


def test_no_proof_is_left_as_sorry():
    assert not [path.name for path in LEAN.joinpath("Nary").rglob("*.lean") if "sorry" in path.read_text(encoding="utf-8")]


def test_mathlib_is_the_version_of_the_lean_toolchain():
    version = LEAN.joinpath("lean-toolchain").read_text(encoding="utf-8").strip().split(":")[1]
    assert f'rev = "{version}"' in LEAN.joinpath("lakefile.toml").read_text(encoding="utf-8")
