"""The domains of partial functions, recorded with nary.domains."""

import doctest

import nary.domains
import pytest
from nary import NumberKind, Pow, log, sin, tan
from nary.domains import domain, set_domain
from nary.logic import true

x, y = NumberKind("x"), NumberKind("y")


def test_docstring_examples():
    result = doctest.testmod(nary.domains)
    assert result.attempted > 0
    assert result.failed == 0


def test_declared_domains():
    assert repr(domain(log)(x)) == "Ne(x, 0)"
    assert repr(domain(tan)(x)) == "Ne(cos(x), 0)"
    # x / y is Mul(x, Pow(y, -1)): this is where division by zero is excluded.
    assert repr(domain(Pow)(y, -1)) == "Or(Ne(y, 0), Gt(re(-1), 0))"
    assert domain(sin) is None


def test_domain_errors():
    with pytest.raises(TypeError, match="domain expects a declared function, got x"):
        domain(x)
    with pytest.raises(TypeError, match="set_domain expects a declared function, got x"):
        set_domain(x, lambda a: true)
    with pytest.raises(TypeError, match="must be a Python function, got true"):
        set_domain(sin, true)
    with pytest.raises(ValueError, match="the domain of log is already set"):
        set_domain(log, lambda a: true)
