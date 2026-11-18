"""The domains of partial functions, declared with declare_function."""

import doctest

import nary.domains
import pytest
from nary import NumberKind, Pow, declare_function, log, sin, tan
from nary.calculus import Integral
from nary.domains import domain
from nary.logic import true

x, y = NumberKind("x"), NumberKind("y")


def test_docstring_examples():
    result = doctest.testmod(nary.domains)
    assert result.attempted > 0
    assert result.failed == 0


def test_declared_domains():
    assert domain(sin)(x) == true
    assert repr(domain(log)(x)) == "Ne(x, 0)"
    assert repr(domain(tan)(x)) == "Ne(cos(x), 0)"
    # x / y is Mul(x, Pow(y, -1)): this is where division by zero is excluded.
    assert repr(domain(Pow)(y, -1)) == "Or(Ne(y, 0), Gt(re(-1), 0))"
    assert domain(Integral) is None


def test_declare_function_needs_a_domain():
    with pytest.raises(TypeError, match="domain"):
        declare_function("f", NumberKind, returns=NumberKind)
    f = declare_function("f", NumberKind, returns=NumberKind, domain=None)
    assert domain(f) is None
    with pytest.raises(TypeError, match="must be a Python function or None, got true"):
        declare_function("f", NumberKind, returns=NumberKind, domain=true)
    with pytest.raises(TypeError, match="domain expects a declared function, got x"):
        domain(x)
