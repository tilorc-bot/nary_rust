import nary.domains
import pytest
from nary import BoolKind, Bound, Eq, Lambda, Many, Ne, NumberKind, Pow, declare_function, log, sin, tan
from nary.calculus import Derivative, Integral
from nary.domains import domain, domain_of
from nary.logic import true

x, y = NumberKind("x"), NumberKind("y")


def test_declared_domains():
    assert domain(sin) == true
    assert repr(domain(log)) == "Ne(arg, 0)"
    assert repr(domain(tan)) == "Ne(cos(arg), 0)"
    assert repr(domain(nary.Lt)) == "And(Eq(re(lhs), lhs), Eq(re(rhs), rhs))"
    assert domain(Derivative) == true and domain(Lambda(x, x).head) == true
    assert domain(Integral) is None


def test_the_domain_of_an_application():
    assert repr(domain_of(Pow(y, -1))) == "Or(Ne(y, 0), Gt(re(-1), 0))"
    base, exp = NumberKind("base"), NumberKind("exp")
    assert repr(domain_of(Pow(exp, base))) == "Or(Ne(exp, 0), Gt(re(base), 0))"
    assert repr(domain_of(tan(log(x)))) == "Ne(cos(log(x)), 0)"
    assert domain_of(Integral(sin, 0, x)) is None
    with pytest.raises(TypeError, match="expects an application of a declared function, got x"):
        domain_of(x)


def test_what_a_declaration_refuses():
    with pytest.raises(TypeError, match="domain"):
        declare_function("f", x, returns=NumberKind)
    for not_a_domain in (lambda x: Ne(x, 0), None, True, x + 1):
        with pytest.raises(TypeError, match="the domain of f must be a BoolKind expression"):
            declare_function("f", x, returns=NumberKind, domain=not_a_domain)
    with pytest.raises(ValueError, match="mentions y, which is not one of its parameters"):
        declare_function("f", x, returns=NumberKind, domain=Ne(y, 0))
    with pytest.raises(ValueError, match="mentions x, which is not one of its parameters"):
        declare_function("f", BoolKind("x"), returns=NumberKind, domain=Eq(x, 0))
    with pytest.raises(ValueError, match="mentions x, which is not one of its parameters"):
        declare_function("f", Many(x), returns=NumberKind, domain=Ne(x, 0))
    with pytest.raises(ValueError, match="mentions x, which is not one of its parameters"):
        declare_function("f", Bound(x), returns=NumberKind, domain=Ne(x, 0))
    with pytest.raises(ValueError, match="f has two parameters named x"):
        declare_function("f", x, BoolKind("x"), returns=NumberKind, domain=true)
    with pytest.raises(TypeError, match="domain expects a declared function, got x"):
        domain(x)
