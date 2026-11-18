"""Printing expressions as Lean terms, with nary.lean. Lean itself is not
needed: lean/check_printer.py checks the output with Lean, by hand."""

import doctest

import nary as nr
import nary.lean
import pytest
from nary.calculus import Derivative, Integral, NumberFunction
from nary.lean import to_lean, to_lean_example
from nary.logic import And, Not, true
from nary.matrices import Matrix, Trace

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
    other_sin = nr.declare_function("sin", nr.NumberKind, returns=nr.NumberKind)
    with pytest.raises(ValueError, match="^sin has no Lean definition"):
        to_lean(other_sin(x))
    with pytest.raises(ValueError, match="only a Lambda of one NumberKind variable"):
        to_lean(nr.Lambda((x, y), x * y))
    with pytest.raises(ValueError, match="two free symbols are named x"):
        to_lean_example(And(nr.BoolKind("x"), x < 1))
    with pytest.raises(ValueError, match="a symbol named some cannot be written in Lean"):
        to_lean(nr.NumberKind("some"))
