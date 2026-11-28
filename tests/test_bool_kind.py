import copy
import pickle

import nary as nr
import pytest
from nary import BoolKind, NumberKind, _core, declare_constant, declare_kind
from nary.lean import to_lean
from nary.logic import And, Not, Or, false, true

x, p = NumberKind("x"), BoolKind("p")


def test_bool_kind_of_true_is_the_constant_true():
    assert BoolKind(True) is true


def test_bool_kind_of_false_is_the_constant_false():
    assert BoolKind(False) is false


def test_bool_kind_of_true_equals_true_and_has_its_hash():
    assert BoolKind(True) == true and hash(BoolKind(True)) == hash(true)


def test_bool_kind_of_a_python_comparison_is_true():
    assert BoolKind(1 < 2) is true  # noqa: PLR0133


def test_bool_kind_of_a_structural_equality_is_false():
    assert BoolKind(x == 0) is false


def test_bool_kind_of_a_bool_is_accepted_as_an_argument():
    assert Or(p, BoolKind(True)) == Or(p, true)


def test_true_and_false_print_as_before():
    assert (repr(true), repr(false)) == ("true", "false")


def test_true_and_false_are_constants_and_not_literals():
    assert (true.is_constant, true.is_literal, true.value) == (True, False, None)
    assert (false.is_constant, false.is_literal, false.value) == (True, False, None)


def test_true_and_false_are_different_and_are_not_python_bools():
    assert true != false and true != True and false != False


def test_true_and_false_print_in_lean_as_before():
    assert (to_lean(true), to_lean(false)) == ("Nary.true", "Nary.false")


def test_true_is_not_pickled_as_before():
    with pytest.raises(TypeError, match="^cannot pickle 'nary.Expr' object$"):
        pickle.dumps(true)


def test_true_is_not_copied_as_before():
    with pytest.raises(TypeError, match="^cannot pickle 'nary.Expr' object$"):
        copy.copy(true)


def test_bool_kind_of_a_str_is_a_symbol():
    assert (p.is_symbol, p.name, p.kind, repr(p)) == (True, "p", BoolKind, "p")


def test_and_rejects_a_python_bool_argument():
    with pytest.raises(TypeError, match="^And expects BoolKind, got bool: True$"):
        And(p, True)


def test_or_rejects_a_structural_equality_argument():
    with pytest.raises(TypeError, match="^Or expects BoolKind, got bool: False$"):
        Or(x == 0, p)


def test_not_rejects_a_python_bool_argument():
    with pytest.raises(TypeError, match="^Not expects BoolKind, got bool: False$"):
        Not(False)


def test_number_kind_rejects_a_python_bool():
    with pytest.raises(TypeError, match=r"^NumberKind takes a name \(a str\) or a literal of type int or Fraction, got bool: True$"):
        NumberKind(True)


def test_bool_kind_rejects_the_int_1():
    with pytest.raises(TypeError, match=r"^BoolKind takes a name \(a str\) or True or False, got int: 1$"):
        BoolKind(1)


def test_bool_kind_rejects_the_int_0():
    with pytest.raises(TypeError, match=r"^BoolKind takes a name \(a str\) or True or False, got int: 0$"):
        BoolKind(0)


def test_bool_kind_rejects_none():
    with pytest.raises(TypeError, match=r"^BoolKind takes a name \(a str\) or True or False, got NoneType: None$"):
        BoolKind(None)


def test_a_declared_kind_rejects_a_python_bool():
    with pytest.raises(TypeError, match=r"^SetKind takes a name \(a str\), got bool: True; it accepts no literals$"):
        declare_kind("SetKind")(True)


def test_a_kind_with_bool_literals_still_makes_a_literal():
    bit = declare_kind("BitKind", literals=bool)(True)
    assert (bit.is_literal, bit.value, repr(bit)) == (True, True, "True")


def test_the_expression_returned_for_a_value_must_be_of_the_kind():
    with pytest.raises(TypeError, match="^expected BoolKind, got 1$"):
        _core._calling_with_returns(BoolKind, None, nr.NumberKind(1))


def test_the_core_returns_the_expression_registered_for_a_value_of_any_kind():
    SetKind = declare_kind("SetKind")
    empty = declare_constant("empty", SetKind)
    _core._calling_with_returns(SetKind, None, empty)
    assert SetKind(None) is empty
