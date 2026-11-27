import pytest

from nary import Add, Mul, NumberKind
from nary.arithmetic_rules import rules
from nary.rewriting import rewrite

x, y, z = (NumberKind(name) for name in "xyz")


def test_order_of_arguments_does_not_matter_at_the_top():
    assert rewrite(Add(x, y, Mul(-1, x)), rules) == y
    assert rewrite(Add(Mul(x, -1), y, x), rules) == y
    assert rewrite(Mul(0, x, y), rules) == rewrite(Mul(y, x, 0), rules) == NumberKind(0)


@pytest.mark.xfail(strict=True, reason="a + a compares arguments syntactically, so 2*x and x*2 differ")
def test_equal_up_to_order_arguments_combine():
    assert rewrite(Mul(x, 2) + Mul(2, x), rules) == rewrite(Mul(2, x) + Mul(2, x), rules)


@pytest.mark.xfail(strict=True, reason="only one level of nested Add is flattened before matching")
def test_flattening_reaches_every_level():
    assert rewrite(Add(x, Add(y, Add(x, z))), rules) == rewrite(Add(x, y, x, z), rules)


@pytest.mark.xfail(strict=True, reason="a + a and a + -1*a overlap, and inner brackets decide which applies")
def test_bracketing_does_not_change_the_result():
    assert rewrite(Add(x, Add(x, Mul(-1, x))), rules) == rewrite(Add(x, x, Mul(-1, x)), rules)
