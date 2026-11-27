from fractions import Fraction

import pytest

from nary import Add, Mul, NumberKind, Pow, log, sin
from nary.arithmetic_rules import rules
from nary.rewriting import rewrite

pytestmark = pytest.mark.fuzz

symbols = [NumberKind(name) for name in "xyz"]
literals = [NumberKind(n) for n in (0, 1, -1, 2)]


def polynomial(rng, depth=3):
    if depth == 0 or rng.random() < 0.3:
        return rng.choice(symbols + literals)
    if rng.random() < 0.1:
        return Pow(polynomial(rng, depth - 1), rng.choice([0, 1, 2]))
    head = rng.choice([Add, Mul])
    return head(*(polynomial(rng, depth - 1) for _ in range(rng.randint(2, 4))))


def with_partial_parts(rng, depth=3):
    if depth == 0 or rng.random() < 0.3:
        leaves = symbols + literals + [log(symbols[0]), sin(symbols[1])]
        return rng.choice(leaves)
    if rng.random() < 0.15:
        return Pow(with_partial_parts(rng, depth - 1), rng.choice([-1, 0, 1]))
    head = rng.choice([Add, Mul])
    return head(*(with_partial_parts(rng, depth - 1) for _ in range(rng.randint(2, 4))))


def rebuilt(e, args):
    return e if e.is_atom else e.head(*args)


def shuffled(e, rng):
    if e.is_atom:
        return e
    args = [shuffled(arg, rng) for arg in e.args]
    if e.head.is_commutative:
        rng.shuffle(args)
    return e.head(*args)


def flat_args(head, e):
    if e.is_atom or e.head != head:
        return [e]
    return [leaf for arg in e.args for leaf in flat_args(head, arg)]


def bracketed(head, args, rng):
    if len(args) <= 2 or rng.random() < 0.3:
        return head(*args)
    i = rng.randrange(len(args) - 1)
    j = rng.randrange(i + 2, len(args) + 1)
    if j - i == len(args):
        return head(*args)
    return bracketed(head, [*args[:i], head(*args[i:j]), *args[j:]], rng)


def rebracketed(e, rng):
    if e.is_atom:
        return e
    if e.head.is_associative:
        return bracketed(e.head, [rebracketed(arg, rng) for arg in flat_args(e.head, e)], rng)
    return e.head(*(rebracketed(arg, rng) for arg in e.args))


def canonical(e):
    if e.is_atom:
        return repr(e)
    args = flat_args(e.head, e) if e.head.is_associative else e.args
    keys = [canonical(arg) for arg in args]
    if e.head.is_commutative:
        keys.sort()
    return f"{e.head!r}({', '.join(keys)})"


def value(e, at):
    if e.is_literal:
        return Fraction(e.value)
    if e.is_symbol:
        return at[e]
    args = [value(arg, at) for arg in e.args]
    if e.head == Add:
        return sum(args, Fraction(0))
    if e.head == Mul:
        product = Fraction(1)
        for arg in args:
            product *= arg
        return product
    if e.head == Pow:
        return args[0] ** args[1]
    raise ValueError(f"no value for {e!r}")


def assignment(rng):
    return {s: Fraction(rng.randint(-9, 9), rng.randint(1, 5)) for s in symbols}


@pytest.mark.xfail(reason="test_equal_up_to_order_arguments_combine fails")
def test_shuffling_commutative_arguments_does_not_change_the_rewritten_result(fuzz):
    def holds(e, rng):
        other = shuffled(e, rng)
        a, b = rewrite(e, rules), rewrite(other, rules)
        return canonical(a) == canonical(b) or f"{other!r} rewrites to {b!r}, not {a!r}"

    fuzz.check(with_partial_parts, holds)


def test_rewriting_keeps_the_value(fuzz):
    def holds(e, rng):
        other = rebracketed(shuffled(e, rng), rng)
        result = rewrite(other, rules)
        for _ in range(3):
            at = assignment(rng)
            if value(result, at) != value(e, at):
                return f"{other!r} rewrites to {result!r}, which differs at {at}"
        return True

    fuzz.check(polynomial, holds)


@pytest.mark.xfail(reason="test_flattening_reaches_every_level and test_bracketing_does_not_change_the_result fail")
def test_rebracketing_does_not_change_the_rewritten_result(fuzz):
    def holds(e, rng):
        other = rebracketed(e, rng)
        a, b = rewrite(e, rules), rewrite(other, rules)
        return canonical(a) == canonical(b) or f"{other!r} rewrites to {b!r}, not {a!r}"

    fuzz.check(polynomial, holds)


def test_rewriting_twice_is_rewriting_once(fuzz):
    def holds(e, rng):
        once = rewrite(e, rules)
        twice = rewrite(once, rules)
        return twice == once or f"{once!r} rewrites again to {twice!r}"

    fuzz.check(with_partial_parts, holds)
