import nary as nr
import pytest
from nary import BoolKind, NumberKind
from nary.logic import And, Not, Or, false, true

x, y = NumberKind("x"), NumberKind("y")


def test_elementary_functions():
    e = nr.log(nr.exp(nr.tan(nr.cos(x))))
    assert repr(e) == "log(exp(tan(cos(x))))"
    assert e.kind is NumberKind


def test_connectives_and_constants():
    e = Or(And(x < y, true), Not(nr.Eq(x, y)), false)
    assert repr(e) == "Or(And(Lt(x, y), true), Not(Eq(x, y)), false)"
    assert e.kind is BoolKind
    assert true.kind is BoolKind and true.args == () and true != false
    assert "And" not in nr.__all__


def test_python_bool_is_not_a_boolkind():
    with pytest.raises(TypeError, match=r"^And expects BoolKind, got bool: True$"):
        And(x < y, True)
