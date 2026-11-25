<!-- Written by `python -m scoreboard.report`; do not edit. -->
# SymPy's `sympy/core/tests/test_power.py` on nary

SymPy 1.14.0. 290 cases: one for each `==` or `!=` that an assert makes when the test runs.

| | passing |
|---|---|
| cases nary can write, differences left out | 16 of 86 (19%) |
| the same, with the cases nary cannot write yet | 16 of 189 (8%) |

| pile | cases | meaning |
|---|---|---|
| pass | 16 | nary's engine agrees with SymPy |
| gap | 70 | nary can write both sides, and its engine does not agree with SymPy yet |
| differs | 1 | nary does not agree with SymPy, for a stated reason; not counted against nary |
| not expressible yet | 103 | a test of a value that needs something nary cannot write |
| not applicable | 91 | not a test of the value of an expression (a query, printing, an error) |
| not run | 9 | the scoreboard could not run it; a limit of the scoreboard, not of nary |

Passing, by how: 13 where nary keeps the two sides apart, as SymPy does; 2 where the two sides are the same expression as written; 1 where the engine rewrites the two sides to the same expression.

## Gaps, by test function: 70

**test_better_sqrt** (23)

- [test_better_sqrt:L442](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L442) `sqrt(3 + 4 * I) == 2 + I`, in nary `Pow(Add(3, Mul(4, I)), Pow(2, -1)) == Add(2, I)`
- [test_better_sqrt:L443](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L443) `sqrt(3 - 4 * I) == 2 - I`, in nary `Pow(Add(3, Mul(-1, Mul(4, I))), Pow(2, -1)) == Add(2, Mul(-1, I))`
- [test_better_sqrt:L444](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L444) `sqrt(-3 - 4 * I) == 1 - 2 * I`, in nary `Pow(Add(-3, Mul(-1, Mul(4, I))), Pow(2, -1)) == Add(1, Mul(-1, Mul(2, I)))`
- [test_better_sqrt:L445](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L445) `sqrt(-3 + 4 * I) == 1 + 2 * I`, in nary `Pow(Add(-3, Mul(4, I)), Pow(2, -1)) == Add(1, Mul(2, I))`
- [test_better_sqrt:L446](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L446) `sqrt(32 + 24 * I) == 6 + 2 * I`, in nary `Pow(Add(32, Mul(24, I)), Pow(2, -1)) == Add(6, Mul(2, I))`
- [test_better_sqrt:L447](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L447) `sqrt(32 - 24 * I) == 6 - 2 * I`, in nary `Pow(Add(32, Mul(-1, Mul(24, I))), Pow(2, -1)) == Add(6, Mul(-1, Mul(2, I)))`
- [test_better_sqrt:L448](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L448) `sqrt(-32 - 24 * I) == 2 - 6 * I`, in nary `Pow(Add(-32, Mul(-1, Mul(24, I))), Pow(2, -1)) == Add(2, Mul(-1, Mul(6, I)))`
- [test_better_sqrt:L449](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L449) `sqrt(-32 + 24 * I) == 2 + 6 * I`, in nary `Pow(Add(-32, Mul(24, I)), Pow(2, -1)) == Add(2, Mul(6, I))`
- [test_better_sqrt:L454](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L454) `sqrt((3 + 4 * I) / 4) == 1 + I / 2`, in nary `Pow(Mul(Add(3, Mul(4, I)), Pow(4, -1)), Pow(2, -1)) == Add(1, Mul(I, Pow(2, -1)))`
- [test_better_sqrt:L458](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L458) `sqrt((8 + 15 * I) / 8) == (5 + 3 * I) / 4`, in nary `Pow(Mul(Add(8, Mul(15, I)), Pow(8, -1)), Pow(2, -1)) == Mul(Add(5, Mul(3, I)), Pow(4, -1))`
- [test_better_sqrt:L460](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L460) `sqrt((3 - 4 * I) / 25) == (2 - I) / 5`, in nary `Pow(Mul(Add(3, Mul(-1, Mul(4, I))), Pow(25, -1)), Pow(2, -1)) == Mul(Add(2, Mul(-1, I)), Pow(5, -1))`
- [test_better_sqrt:L461](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L461) `sqrt((3 - 4 * I) / 26) == (2 - I) / sqrt(26)`, in nary `Pow(Mul(Add(3, Mul(-1, Mul(4, I))), Pow(26, -1)), Pow(2, -1)) == Mul(Add(2, Mul(-1, I)), Pow(Pow(26, Pow(2, -1)), -1))`
- [test_better_sqrt:L464](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L464) `sqrt((3 + 4 * I) / (3 - 4 * I)) == (3 + 4 * I) / 5`, in nary `Pow(Mul(Add(3, Mul(4, I)), Pow(Add(3, Mul(-1, Mul(4, I))), -1)), Pow(2, -1)) == Mul(Add(3, Mul(4, I)), Pow(5, -1))`
- [test_better_sqrt:L465](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L465) `sqrt(2 / (3 + 4 * I)) == sqrt(2) / 5 * (2 - I)`, in nary `Pow(Mul(2, Pow(Add(3, Mul(4, I)), -1)), Pow(2, -1)) == Mul(Mul(Pow(2, Pow(2, -1)), Pow(5, -1)), Add(2, Mul(-1, I)))`
- [test_better_sqrt:L467](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L467) `sqrt(-2 / (3 + 4 * I)) == sqrt(2) / 5 * (1 + 2 * I)`, in nary `Pow(Mul(-2, Pow(Add(3, Mul(4, I)), -1)), Pow(2, -1)) == Mul(Mul(Pow(2, Pow(2, -1)), Pow(5, -1)), Add(1, Mul(2, I)))`
- [test_better_sqrt:L470](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L470) `sqrt(1 / (3 + I * 4)) == (2 - I) / 5`, in nary `Pow(Mul(1, Pow(Add(3, Mul(I, 4)), -1)), Pow(2, -1)) == Mul(Add(2, Mul(-1, I)), Pow(5, -1))`
- [test_better_sqrt:L471](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L471) `sqrt(1 / (3 - I)) == sqrt(10) * sqrt(3 + I) / 10`, in nary `Pow(Mul(1, Pow(Add(3, Mul(-1, I)), -1)), Pow(2, -1)) == Mul(Mul(Pow(10, Pow(2, -1)), Pow(Add(3, I), Pow(2, -1))), Pow(10, -1))`
- [test_better_sqrt:L476](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L476) `sqrt(3 + 4 * I) ** 3 == (2 + I) ** 3`, in nary `Pow(Pow(Add(3, Mul(4, I)), Pow(2, -1)), 3) == Pow(Add(2, I), 3)`
- [test_better_sqrt:L477](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L477) `Pow(3 + 4 * I, Rational(3, 2)) == 2 + 11 * I`, in nary `Pow(Add(3, Mul(4, I)), Mul(3, Pow(2, -1))) == Add(2, Mul(11, I))`
- [test_better_sqrt:L478](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L478) `Pow(6 + 8 * I, Rational(3, 2)) == 2 * sqrt(2) * (2 + 11 * I)`, in nary `Pow(Add(6, Mul(8, I)), Mul(3, Pow(2, -1))) == Mul(Mul(2, Pow(2, Pow(2, -1))), Add(2, Mul(11, I)))`
- [test_better_sqrt:L489](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L489) `sqrt(2 * I) == 1 + I`, in nary `Pow(Mul(2, I), Pow(2, -1)) == Add(1, I)`
- [test_better_sqrt:L491](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L491) `Pow(2 * I, 3 * S.Half) == (1 + I) ** 3`, in nary `Pow(Mul(2, I), Mul(3, Pow(2, -1))) == Pow(Add(1, I), 3)`
- [test_better_sqrt:L495](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L495) `Pow(Rational(-9, 2) * I, Rational(3, 2)) == 27 * (1 - I) ** 3 / 8`, in nary `Pow(Mul(Mul(-9, Pow(2, -1)), I), Mul(3, Pow(2, -1))) == Mul(Mul(27, Pow(Add(1, Mul(-1, I)), 3)), Pow(8, -1))`

**test_issue_7638** (12)

- [test_issue_7638:L384](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L384) `(1 + I) ** (4 * I * f) == ((1 + I) ** (12 * I * f)) ** Rational(1, 3)`, in nary `Pow(Add(1, I), Mul(Mul(4, I), Mul(pi, Pow(log(Pow(2, Pow(2, -1))), -1)))) == Pow(Pow(Add(1, I), Mul(Mul(12, I), Mul(pi, Pow(log(Pow(2, Pow(2, -1))), -1)))), Pow(3, -1))`: to review: the numerical check finds different values (SymPy is wrong, or the check is)
- [test_issue_7638:L392](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L392) `cbrt(p ** 2) == p ** Rational(2, 3)`, in nary `Pow(Pow(p, 2), Pow(3, -1)) == Pow(p, Mul(2, Pow(3, -1)))`
- [test_issue_7638:L394](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L394) `sqrt(1 / (1 + I)) == sqrt(1 - I) / sqrt(2)`, in nary `Pow(Mul(1, Pow(Add(1, I), -1)), Pow(2, -1)) == Mul(Pow(Add(1, Mul(-1, I)), Pow(2, -1)), Pow(Pow(2, Pow(2, -1)), -1))`
- [test_issue_7638:L396](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L396) `sqrt(e) == I / sqrt(-1 + sqrt(2))`, in nary `Pow(Mul(1, Pow(Add(1, Mul(-1, Pow(2, Pow(2, -1)))), -1)), Pow(2, -1)) == Mul(I, Pow(Pow(Add(-1, Pow(2, Pow(2, -1))), Pow(2, -1)), -1))`
- [test_issue_7638:L397](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L397) `e ** Rational(-1, 2) == -I * sqrt(-1 + sqrt(2))`, in nary `Pow(Mul(1, Pow(Add(1, Mul(-1, Pow(2, Pow(2, -1)))), -1)), Mul(-1, Pow(2, -1))) == Mul(Mul(-1, I), Pow(Add(-1, Pow(2, Pow(2, -1))), Pow(2, -1)))`
- [test_issue_7638:L401](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L401) `sqrt((p + I) ** Rational(4, 3)) == (p + I) ** Rational(2, 3)`, in nary `Pow(Pow(Add(p, I), Mul(4, Pow(3, -1))), Pow(2, -1)) == Pow(Add(p, I), Mul(2, Pow(3, -1)))`
- [test_issue_7638:L404](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L404) `sqrt(q ** 2) == q`, in nary `Pow(Pow(Add(1, I), 2), Pow(2, -1)) == Add(1, I)`
- [test_issue_7638:L404#1](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L404) `sqrt(q ** 2) == q`, in nary `Pow(Pow(Add(1, Mul(-1, I)), 2), Pow(2, -1)) == Add(1, Mul(-1, I))`
- [test_issue_7638:L406](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L406) `sqrt(q ** 2) == -q`, in nary `Pow(Pow(Add(-1, I), 2), Pow(2, -1)) == Mul(-1, Add(-1, I))`
- [test_issue_7638:L406#1](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L406) `sqrt(q ** 2) == -q`, in nary `Pow(Pow(Add(-1, Mul(-1, I)), 2), Pow(2, -1)) == Mul(-1, Add(-1, Mul(-1, I)))`
- [test_issue_7638:L410](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L410) `sqrt(e ** 5) == e ** (5 * S.Half)`, in nary `Pow(Pow(Add(1, Mul(I, Pow(5, -1))), 5), Pow(2, -1)) == Pow(Add(1, Mul(I, Pow(5, -1))), Mul(5, Pow(2, -1)))`
- [test_issue_7638:L411](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L411) `sqrt(e ** 6) == e ** 3`, in nary `Pow(Pow(Add(1, Mul(I, Pow(5, -1))), 6), Pow(2, -1)) == Pow(Add(1, Mul(I, Pow(5, -1))), 3)`

**test_powers_of_I** (12)

- [test_powers_of_I:L646](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 0) == 1`
- [test_powers_of_I:L646#2](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 2) == I`
- [test_powers_of_I:L646#4](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 4) == -1`
- [test_powers_of_I:L646#5](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 5) == Mul(-1, Pow(I, Pow(2, -1)))`
- [test_powers_of_I:L646#6](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 6) == Mul(-1, I)`
- [test_powers_of_I:L646#7](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 7) == Mul(-1, Pow(Pow(I, Pow(2, -1)), 3))`
- [test_powers_of_I:L646#8](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 8) == 1`
- [test_powers_of_I:L646#9](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 9) == Pow(I, Pow(2, -1))`
- [test_powers_of_I:L646#10](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 10) == I`
- [test_powers_of_I:L646#11](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 11) == Pow(Pow(I, Pow(2, -1)), 3)`
- [test_powers_of_I:L646#12](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 12) == -1`
- [test_powers_of_I:L649](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L649) `sqrt(I) ** (S(9) / 2) == -I ** (S(1) / 4)`, in nary `Pow(Pow(I, Pow(2, -1)), Mul(9, Pow(2, -1))) == Mul(-1, Pow(I, Mul(1, Pow(4, -1))))`

**test_rational** (6)

- [test_rational:L27](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L27) `sqrt(a) == r`, in nary `Pow(Pow(5, -1), Pow(2, -1)) == Mul(Pow(5, Pow(2, -1)), Pow(5, -1))`
- [test_rational:L28](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L28) `2 * sqrt(a) == 2 * r`, in nary `Mul(2, Pow(Pow(5, -1), Pow(2, -1))) == Mul(2, Mul(Pow(5, Pow(2, -1)), Pow(5, -1)))`
- [test_rational:L31](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L31) `a ** Rational(3, 2) == r`, in nary `Pow(Pow(5, -1), Mul(3, Pow(2, -1))) == Mul(Pow(5, -1), Pow(Pow(5, -1), Pow(2, -1)))`
- [test_rational:L32](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L32) `2 * a ** Rational(3, 2) == 2 * r`, in nary `Mul(2, Pow(Pow(5, -1), Mul(3, Pow(2, -1)))) == Mul(2, Mul(Pow(5, -1), Pow(Pow(5, -1), Pow(2, -1))))`
- [test_rational:L35](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L35) `a ** Rational(17, 3) == r`, in nary `Pow(Pow(5, -1), Mul(17, Pow(3, -1))) == Mul(Pow(Pow(5, -1), 5), Pow(Pow(5, -1), Mul(2, Pow(3, -1))))`
- [test_rational:L36](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L36) `2 * a ** Rational(17, 3) == 2 * r`, in nary `Mul(2, Pow(Pow(5, -1), Mul(17, Pow(3, -1)))) == Mul(2, Mul(Pow(Pow(5, -1), 5), Pow(Pow(5, -1), Mul(2, Pow(3, -1)))))`

**test_issue_3449** (5)

- [test_issue_3449:L58](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L58) `(x ** Rational(1, 3)) ** Rational(2) == x ** Rational(2, 3)`, in nary `Pow(Pow(x, Pow(3, -1)), 2) == Pow(x, Mul(2, Pow(3, -1)))`
- [test_issue_3449:L75](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L75) `Number(5) ** Rational(2, 3) == Number(25) ** Rational(1, 3)`, in nary `Pow(5, Mul(2, Pow(3, -1))) == Pow(25, Pow(3, -1))`
- [test_issue_3449:L81](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L81) `(a ** 3) ** Rational(2, 5) == a ** Rational(6, 5)`, in nary `Pow(Pow(a, 3), Mul(2, Pow(5, -1))) == Pow(a, Mul(6, Pow(5, -1)))`
- [test_issue_3449:L82](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L82) `(a ** 2) ** b == (a ** b) ** 2`, in nary `Pow(Pow(a, 2), b) == Pow(Pow(a, b), 2)`
- [test_issue_3449:L83](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L83) `(a ** Rational(2, 3)) ** x == a ** (x * Rational(2, 3)) != (a ** x) ** Rational(2, 3)`, in nary `Pow(Pow(a, Mul(2, Pow(3, -1))), x) == Pow(a, Mul(x, Mul(2, Pow(3, -1))))`

**test_issue_6208** (4)

- [test_issue_6208:L333](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L333) `sqrt(33 ** (I * 9 / 10)) == -33 ** (I * 9 / 20)`, in nary `Pow(Pow(33, Mul(Mul(I, 9), Pow(10, -1))), Pow(2, -1)) == Mul(-1, Pow(33, Mul(Mul(I, 9), Pow(20, -1))))`
- [test_issue_6208:L336](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L336) `sqrt(exp(3 * I)) == exp(3 * I / 2)`, in nary `Pow(exp(Mul(3, I)), Pow(2, -1)) == exp(Mul(Mul(3, I), Pow(2, -1)))`
- [test_issue_6208:L337](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L337) `sqrt(-sqrt(3) * (1 + 2 * I)) == sqrt(sqrt(3)) * sqrt(-1 - 2 * I)`, in nary `Pow(Mul(Mul(-1, Pow(3, Pow(2, -1))), Add(1, Mul(2, I))), Pow(2, -1)) == Mul(Pow(Pow(3, Pow(2, -1)), Pow(2, -1)), Pow(Add(-1, Mul(-1, Mul(2, I))), Pow(2, -1)))`
- [test_issue_6208:L338](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L338) `sqrt(exp(5 * I)) == -exp(5 * I / 2)`, in nary `Pow(exp(Mul(5, I)), Pow(2, -1)) == Mul(-1, exp(Mul(Mul(5, I), Pow(2, -1))))`

**test_rational_powers_larger_than_one** (3)

- [test_rational_powers_larger_than_one:L615](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L615) `Rational(2, 3) ** Rational(3, 2) == 2 * sqrt(6) / 9`, in nary `Pow(Mul(2, Pow(3, -1)), Mul(3, Pow(2, -1))) == Mul(Mul(2, Pow(6, Pow(2, -1))), Pow(9, -1))`
- [test_rational_powers_larger_than_one:L616](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L616) `Rational(1, 6) ** Rational(9, 4) == 6 ** Rational(3, 4) / 216`, in nary `Pow(Pow(6, -1), Mul(9, Pow(4, -1))) == Mul(Pow(6, Mul(3, Pow(4, -1))), Pow(216, -1))`
- [test_rational_powers_larger_than_one:L617](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L617) `Rational(3, 7) ** Rational(7, 3) == 9 * 3 ** Rational(1, 3) * 7 ** Rational(2, 3) / 343`, in nary `Pow(Mul(3, Pow(7, -1)), Mul(7, Pow(3, -1))) == Mul(Mul(Mul(9, Pow(3, Pow(3, -1))), Pow(7, Mul(2, Pow(3, -1)))), Pow(343, -1))`

**test_zero** (2)

- [test_zero:L261](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L261) `0 ** (2 * x) == 0 ** x`, in nary `Pow(0, Mul(2, x)) == Pow(0, x)`
- [test_zero:L266](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L266) `0 ** (2 * x * y) == 0 ** (x * y)`, in nary `Pow(0, Mul(Mul(2, x), y)) == Pow(0, Mul(x, y))`

**test_issue_18190** (1)

- [test_issue_18190:L547](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L547) `sqrt(1 / tan(1 + I)) == 1 / sqrt(tan(1 + I))`, in nary `Pow(Mul(1, Pow(tan(Add(1, I)), -1)), Pow(2, -1)) == Mul(1, Pow(Pow(tan(Add(1, I)), Pow(2, -1)), -1))`

**test_issue_3866** (1)

- [test_issue_3866:L87](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L87) `--sqrt(sqrt(5) - 1) == sqrt(sqrt(5) - 1)`, in nary `Mul(-1, Mul(-1, Pow(Add(Pow(5, Pow(2, -1)), Mul(-1, 1)), Pow(2, -1)))) == Pow(Add(Pow(5, Pow(2, -1)), Mul(-1, 1)), Pow(2, -1))`

**test_large_rational** (1)

- [test_large_rational:L41](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L41) `e == 234232585392159195136 * Rational(1, 7) ** Rational(1, 3)`, in nary `Pow(Add(1835878332164045600327283789016195386006135170226228373525065, Pow(7, -1)), Pow(3, -1)) == Mul(234232585392159195136, Pow(Pow(7, -1), Pow(3, -1)))`

## Differences: 1

**definition: the left side has no value at a point where the other has one** (1)

- [test_negative_one:L93](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L93) `1 / x ** y == x ** (-y)`, in nary `Mul(1, Pow(Pow(x, y), -1)) == Pow(x, Mul(-1, y))`

## Passing: 16

**nary keeps the two sides apart, as SymPy does** (13)

- [test_issue_3449:L65](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L65) `sqrt(1 / a) != 1 / sqrt(a)`, in nary `Pow(Mul(1, Pow(a, -1)), Pow(2, -1)) != Mul(1, Pow(Pow(a, Pow(2, -1)), -1))`
- [test_issue_3449:L66](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L66) `(a ** 3) ** Rational(1, 3) != a`, in nary `Pow(Pow(a, 3), Pow(3, -1)) != a`
- [test_issue_3449:L67](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L67) `(x ** a) ** b != x ** (a * b)`, in nary `Pow(Pow(x, a), b) != Pow(x, Mul(a, b))`
- [test_issue_3449:L83#1](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L83) `(a ** Rational(2, 3)) ** x == a ** (x * Rational(2, 3)) != (a ** x) ** Rational(2, 3)`, in nary `Pow(a, Mul(x, Mul(2, Pow(3, -1)))) != Pow(Pow(a, x), Mul(2, Pow(3, -1)))`
- [test_Pow_signs:L208](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L208) `(3 - y) ** 2 != (y - 3) ** 2`, in nary `Pow(Add(3, Mul(-1, y)), 2) != Pow(Add(y, Mul(-1, 3)), 2)`
- [test_Pow_signs:L210](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L210) `(-3 + y - x) ** 2 != (3 - y + x) ** 2`, in nary `Pow(Add(Add(-3, y), Mul(-1, x)), 2) != Pow(Add(Add(3, Mul(-1, y)), x), 2)`
- [test_Pow_signs:L211](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L211) `(y - 3) ** 3 != -(3 - y) ** 3`, in nary `Pow(Add(y, Mul(-1, 3)), 3) != Mul(-1, Pow(Add(3, Mul(-1, y)), 3))`
- [test_zero:L260](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L260) `0 ** x != 0`, in nary `Pow(0, x) != 0`
- [test_issue_7638:L389](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L389) `cbrt(r ** 3) != r`, in nary `Pow(Pow(r, 3), Pow(3, -1)) != r`
- [test_issue_7638:L390](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L390) `sqrt(Pow(2 * I, 5 * S.Half)) != (2 * I) ** Rational(5, 4)`, in nary `Pow(Pow(Mul(2, I), Mul(5, Pow(2, -1))), Pow(2, -1)) != Pow(Mul(2, I), Mul(5, Pow(4, -1)))`
- [test_issue_7638:L400](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L400) `sqrt(r ** Rational(4, 3)) != r ** Rational(2, 3)`, in nary `Pow(Pow(r, Mul(4, Pow(3, -1))), Pow(2, -1)) != Pow(r, Mul(2, Pow(3, -1)))`
- [test_issue_7638:L408](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L408) `sqrt((p + r * I) ** 2) != p + r * I`, in nary `Pow(Pow(Add(p, Mul(r, I)), 2), Pow(2, -1)) != Add(p, Mul(r, I))`
- [test_issue_7638:L412](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L412) `sqrt((1 + I * r) ** 6) != (1 + I * r) ** 3`, in nary `Pow(Pow(Add(1, Mul(I, r)), 6), Pow(2, -1)) != Pow(Add(1, Mul(I, r)), 3)`

**the two sides are the same expression as written** (2)

- [test_issue_3449:L59](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L59-L60) `(x ** Rational(3)) ** Rational(2, 5) == (x ** Rational(3)) ** Rational(2, 5)`, in nary `Pow(Pow(x, 3), Mul(2, Pow(5, -1))) == Pow(Pow(x, 3), Mul(2, Pow(5, -1)))`
- [test_powers_of_I:L646#3](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 3) == Pow(Pow(I, Pow(2, -1)), 3)`

**the engine rewrites the two sides to the same expression** (1)

- [test_powers_of_I:L646#1](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L646-L648) `[sqrt(I) ** i for i in range(13)] == [1, sqrt(I), I, sqrt(I) ** 3, -1, -sqrt(I), -I, -sqrt(I) ** 3, 1, sqrt(I), I, sqrt(I) ** 3, -1]`, in nary `Pow(Pow(I, Pow(2, -1)), 1) == Pow(I, Pow(2, -1))`

## Not expressible yet: 103

**needs series** (17)

- [test_nseries:L293](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L293) `sqrt(I * x - 1)._eval_nseries(x, 4, None, 1) == I + x / 2 + I * x ** 2 / 8 - x ** 3 / 16 + O(x ** 4)`
- [test_nseries:L294](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L294) `sqrt(I * x - 1)._eval_nseries(x, 4, None, -1) == -I - x / 2 - I * x ** 2 / 8 + x ** 3 / 16 + O(x ** 4)`
- [test_nseries:L295](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L295-L296) `cbrt(I * x - 1)._eval_nseries(x, 4, None, 1) == (-1) ** (S(1) / 3) - (-1) ** (S(5) / 6) * x / 3 + (-1) ** (S(1) / 3) * x ** 2 / 9 + 5 * (-1) ** (S(5) / 6) * x ** 3 / 81 + O(x ** 4)`
- [test_nseries:L297](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L297-L298) `cbrt(I * x - 1)._eval_nseries(x, 4, None, -1) == -(-1) ** (S(2) / 3) - (-1) ** (S(1) / 6) * x / 3 - (-1) ** (S(2) / 3) * x ** 2 / 9 + 5 * (-1) ** (S(1) / 6) * x ** 3 / 81 + O(x ** 4)`
- [test_nseries:L299](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L299) `(1 / (exp(-1 / x) + 1 / x))._eval_nseries(x, 2, None) == x + O(x ** 2)`
- [test_nseries:L301](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L301-L302) `sqrt(-I * x ** 2 + x - 3)._eval_nseries(x, 4, None, 1) == -sqrt(3) * I + sqrt(3) * I * x / 6 - sqrt(3) * I * x ** 2 * (-S(1) / 72 + I / 6) - sqrt(3) * I * x ** 3 * (-S(1) / 432 + I / 36) + O(x ** 4)`
- [test_nseries:L303](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L303-L304) `sqrt(-I * x ** 2 + x - 3)._eval_nseries(x, 4, None, -1) == -sqrt(3) * I + sqrt(3) * I * x / 6 - sqrt(3) * I * x ** 2 * (-S(1) / 72 + I / 6) - sqrt(3) * I * x ** 3 * (-S(1) / 432 + I / 36) + O(x ** 4)`
- [test_nseries:L305](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L305-L307) `cbrt(-I * x ** 2 + x - 3)._eval_nseries(x, 4, None, 1) == -(-1) ** (S(2) / 3) * 3 ** (S(1) / 3) + (-1) ** (S(2) / 3) * 3 ** (S(1) / 3) * x / 9 - (-1) ** (S(2) / 3) * 3 ** (S(1) / 3) * x ** 2 * (-S(1) / 81 + I / 9) - (-1) ** (S(2) / 3) * 3 ** (S(1) / 3) * x ** 3 * (-S(5) / 2187 + 2 * I / 81) + O(x ** 4)`
- [test_nseries:L308](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L308-L310) `cbrt(-I * x ** 2 + x - 3)._eval_nseries(x, 4, None, -1) == -(-1) ** (S(2) / 3) * 3 ** (S(1) / 3) + (-1) ** (S(2) / 3) * 3 ** (S(1) / 3) * x / 9 - (-1) ** (S(2) / 3) * 3 ** (S(1) / 3) * x ** 2 * (-S(1) / 81 + I / 9) - (-1) ** (S(2) / 3) * 3 ** (S(1) / 3) * x ** 3 * (-S(5) / 2187 + 2 * I / 81) + O(x ** 4)`
- [test_issue_6990:L343](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L343-L344) `sqrt(a + b * x + x ** 2).series(x, 0, 3).removeO() == sqrt(a) * x ** 2 * (1 / (2 * a) - b ** 2 / (8 * a ** 2)) + sqrt(a) + b * x / (2 * sqrt(a))`
- [test_issue_6068:L348](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L348-L350) `sqrt(sin(x)).series(x, 0, 7) == sqrt(x) - x ** Rational(5, 2) / 12 + x ** Rational(9, 2) / 1440 - x ** Rational(13, 2) / 24192 + O(x ** 7)`
- [test_issue_6068:L351](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L351-L353) `sqrt(sin(x)).series(x, 0, 9) == sqrt(x) - x ** Rational(5, 2) / 12 + x ** Rational(9, 2) / 1440 - x ** Rational(13, 2) / 24192 - 67 * x ** Rational(17, 2) / 29030400 + O(x ** 9)`
- [test_issue_6068:L354](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L354-L355) `sqrt(sin(x ** 3)).series(x, 0, 19) == x ** Rational(3, 2) - x ** Rational(15, 2) / 12 + x ** Rational(27, 2) / 1440 + O(x ** 19)`
- [test_issue_6068:L356](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L356-L358) `sqrt(sin(x ** 3)).series(x, 0, 20) == x ** Rational(3, 2) - x ** Rational(15, 2) / 12 + x ** Rational(27, 2) / 1440 - x ** Rational(39, 2) / 24192 + O(x ** 20)`
- [test_issue_6782:L362](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L362) `sqrt(sin(x ** 3)).series(x, 0, 7) == x ** Rational(3, 2) + O(x ** 7)`
- [test_issue_6782:L363](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L363) `sqrt(sin(x ** 4)).series(x, 0, 3) == x ** 2 + O(x ** 3)`
- [test_issue_6653:L367](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L367) `(1 / sqrt(1 + sin(x ** 2))).series(x, 0, 3) == 1 - x ** 2 / 2 + O(x ** 3)`

**needs floats** (16)

- [test_issue_3449:L68](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L68) `(x ** 0.5) ** b == x ** (0.5 * b)`
- [test_issue_3449:L69](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L69) `(x ** 0.5) ** 0.5 == x ** 0.25`
- [test_issue_3449:L70](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L70) `(x ** 2.5) ** 0.5 != x ** 1.25`
- [test_issue_3449:L77](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L77) `(x ** 0.5) ** 2 == x ** 1.0`
- [test_zero:L262](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L262) `0 ** (1.0 * x) == 0 ** x`
- [test_zero:L263](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L263) `0 ** (2.0 * x) == 0 ** x`
- [test_zero:L268](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L268) `Float(0) ** 2 is not S.Zero`
- [test_zero:L269](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L269) `Float(0) ** 2 == 0.0`
- [test_issue_6100_12942_4473:L314](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L314) `x ** 1.0 != x`
- [test_issue_6100_12942_4473:L315](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L315) `x != x ** 1.0`
- [test_issue_6100_12942_4473:L316](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L316) `True != x ** 1.0`
- [test_issue_6100_12942_4473:L317](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L317) `x ** 1.0 is not True`
- [test_issue_6100_12942_4473:L319](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L319) `x * y != (x * y) ** 1.0`
- [test_issue_6100_12942_4473:L321](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L321) `(x ** 1.0) ** 1.0 != x`
- [test_issue_6100_12942_4473:L322](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L322) `(x ** 1.0) ** 2.0 != x ** 2`
- [test_issue_7638:L380](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L380) `((1 + I) ** (I * f / 2)) ** 0.3 == (1 + I) ** (0.15 * I * f)`

**needs infinities, nan** (11)

- [test_issue_8582:L416](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L416) `1 ** oo is nan`
- [test_issue_8582:L417](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L417) `1 ** (-oo) is nan`
- [test_issue_8582:L418](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L418) `1 ** zoo is nan`
- [test_issue_8582:L419](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L419) `1 ** (oo + I) is nan`
- [test_issue_8582:L420](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L420) `1 ** (1 + I * oo) is nan`
- [test_issue_8582:L421](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L421) `1 ** (oo + I * oo) is nan`
- [test_issue_13914:L433](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L433) `(-1) ** zoo is nan`
- [test_issue_13914:L434](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L434) `2 ** zoo is nan`
- [test_issue_13914:L435](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L435) `S.Half ** (1 + zoo) is nan`
- [test_issue_13914:L436](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L436) `I ** (zoo + I) is nan`
- [test_issue_13914:L437](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L437) `b ** (I + zoo) is nan`

**needs rewrite** (9)

- [test_power_rewrite_exp:L223](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L223) `(I ** I).rewrite(exp) == exp(-pi / 2)`
- [test_power_rewrite_exp:L233](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L233) `expr.rewrite(exp) == exp((6 + 7 * I) * log(5))`
- [test_power_rewrite_exp:L236](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L236) `Pow(123, 789, evaluate=False).rewrite(exp) == 123 ** 789`
- [test_power_rewrite_exp:L237](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L237) `(1 ** I).rewrite(exp) == 1 ** I`
- [test_power_rewrite_exp:L238](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L238) `(0 ** I).rewrite(exp) == 0 ** I`
- [test_power_rewrite_exp:L241](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L241) `expr.rewrite(exp) == exp((2 + 5 * I) * (log(2) + I * pi))`
- [test_power_rewrite_exp:L244](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L244) `((-2) ** S(-5)).rewrite(exp) == (-2) ** S(-5)`
- [test_power_rewrite_exp:L247](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L247) `(x ** y).rewrite(exp) == exp(y * log(x))`
- [test_power_rewrite_exp:L253](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L253) `(y ** (5 + 6 * I)).rewrite(exp) == exp(log(y) * (5 + 6 * I))`

**needs infinities** (7)

- [test_zero:L265](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L265) `0 ** (x - 2) != S.Infinity ** (2 - x)`
- [test_zero:L267](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L267) `0 ** (-2 * x * y) == S.ComplexInfinity ** (x * y)`
- [test_zero:L274](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L274) `0 ** (-oo) is zoo`
- [test_issue_18509:L569](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L569) `(-oo) ** (-1 + I) is S.Zero`
- [test_issue_18509:L570](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L570) `(-oo) ** (1 + I) is zoo`
- [test_issue_18509:L571](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L571) `oo ** (-1 + I) is S.Zero`
- [test_issue_18509:L572](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L572) `oo ** (1 + I) is zoo`

**needs power** (6)

- [test_power_dispatcher:L635](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L635) `power(2, 3) == 8 * S.One`
- [test_power_dispatcher:L636](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L636) `power(a, 2) == Pow(a, 2)`
- [test_power_dispatcher:L637](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L637) `power(a, a) == Pow(a, a)`
- [test_power_dispatcher:L640](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L640) `power(a, b) == NewPow(a, b)`
- [test_power_dispatcher:L641](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L641) `power(b, a) == NewPow(b, a)`
- [test_power_dispatcher:L642](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L642) `power(b, b) == NewPow(b, b)`

**needs assumption prime=True, infinities** (4)

- [test_issue_18509:L565](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L565) `x ** oo is oo`
- [test_issue_18509:L566](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L566) `(1 / x) ** oo is S.Zero`
- [test_issue_18509:L567](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L567) `(-1 / x) ** oo is S.Zero`
- [test_issue_18509:L568](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L568) `(-x) ** oo is zoo`

**needs floats, series** (4)

- [test_issue_6429:L372](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L372) `f.series(x, x0=0, n=1) == (c ** 2) ** 0.5 + O(x)`
- [test_issue_6429:L373](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L373) `f.taylor_term(0, x) == (c ** 2) ** 0.5`
- [test_issue_6429:L374](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L374) `f.taylor_term(1, x) == 0.5 * x * (c ** 2) ** (-0.5)`
- [test_issue_6429:L375](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L375) `f.taylor_term(2, x) == -0.125 * x ** 2 * (c ** 2) ** (-1.5)`

**needs assumption integer=True** (3)

- [test_issue_3449:L74](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L74) `(x ** k) ** m == x ** (k * m)`
- [test_issue_3449:L78](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L78) `(x ** 2) ** k == (x ** k) ** 2 == x ** (2 * k)`
- [test_issue_3449:L78#1](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L78) `(x ** 2) ** k == (x ** k) ** 2 == x ** (2 * k)`

**needs atan, rewrite** (3)

- [test_power_rewrite_exp:L226](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L226) `expr.rewrite(exp) == exp((4 + 5 * I) * (log(sqrt(13)) + I * atan(Rational(3, 2))))`
- [test_power_rewrite_exp:L230](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L230) `((6 + 7 * I) ** 5).rewrite(exp) == 7225 * sqrt(85) * exp(5 * I * atan(Rational(7, 6)))`
- [test_power_rewrite_exp:L252](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L252) `((2 + 3 * I) ** x).rewrite(exp) == exp(x * (log(sqrt(13)) + I * atan(Rational(3, 2))))`

**needs floats, infinities** (3)

- [test_zero:L270](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L270) `Float(0) ** (-2) is zoo`
- [test_zero:L271](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L271) `Float(0) ** oo is S.Zero`
- [test_zero:L276](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L276) `Float(0) ** (-oo) is zoo`

**needs xreplace** (3)

- [test_issue_21860:L586](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L586) `e.xreplace({x: Rational(3, 8)}) == ans`
- [test_issue_21647:L597](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L597) `e.xreplace({x: 6}) == ans`
- [test_issue_21762:L605](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L605) `e.xreplace({x: S.Half}) == ans`

**needs Abs** (2)

- [test_issue_3449:L64](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L64) `(a ** 2) ** b == (abs(a) ** b) ** 2`
- [test_issue_7638:L388](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L388) `sqrt(r ** 2) == abs(r)`

**needs assumption commutative=False** (2)

- [test_power_with_noncommutative_mul_as_base:L217](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L217) `not (x * y) ** 3 == x ** 3 * y ** 3`
- [test_power_with_noncommutative_mul_as_base:L218](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L218) `(2 * x * y) ** 3 == 8 * (x * y) ** 3`

**needs assumption integer=True, subs** (2)

- [test_better_sqrt:L466](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L466) `sqrt(n / (3 + 4 * I)).subs(n, 2) == sqrt(2) / 5 * (2 - I)`
- [test_better_sqrt:L468](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L468) `sqrt(-n / (3 + 4 * I)).subs(n, 2) == sqrt(2) / 5 * (1 + 2 * I)`

**needs expand** (2)

- [test_expand:L52](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L52) `(2 ** (-1 - x)).expand() == S.Half * 2 ** (-x)`
- [test_better_sqrt:L485](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L485) `eq.expand() == (7 - 24 * I) / 125`

**needs expand, rewrite** (2)

- [test_power_rewrite_exp:L234](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L234) `expr.rewrite(exp).expand() == 15625 * exp(7 * I * log(5))`
- [test_power_rewrite_exp:L242](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L242) `expr.rewrite(exp).expand() == 4 * exp(-5 * pi) * exp(5 * I * log(2))`

**needs Expr, floats** (1)

- [test_issue_6100_12942_4473:L324](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L324) `Pow(b, 1.0, evaluate=False) != b`

**needs assumption even=True** (1)

- [test_Pow_signs:L209](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L209) `(3 - y) ** n != (y - 3) ** n`

**needs assumption imaginary=True** (1)

- [test_better_sqrt:L474](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L474) `sqrt(3 / i) == Mul(sqrt(3), 1 / sqrt(i), evaluate=False)`

**needs atan, expand, rewrite** (1)

- [test_power_rewrite_exp:L227](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L227-L228) `expr.rewrite(exp).expand() == 169 * exp(5 * I * log(13) / 2) * exp(4 * I * atan(Rational(3, 2))) * exp(-5 * atan(Rational(3, 2)))`

**needs expand_multinomial** (1)

- [test_better_sqrt:L484](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L484) `expand_multinomial(eq) == sqrt((-117 + 44 * I) * (3 + 4 * I)) / 125`

**needs floats, subs** (1)

- [test_issue_2993:L536](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L536) `seq == tru`

**needs infinities, power** (1)

- [test_zero:L275](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L275) `power(0, -oo) is zoo`

## Not applicable: 91

**a type query (is_Pow)** (21)

- [test_issue_4362:L119](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L119) `eq.is_Pow and eq.as_numer_denom() == (1, dpos ** 2)`
- [test_issue_4362:L121](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L121) `eq.is_Pow and eq.as_numer_denom() == (1, dneg ** 2)`
- [test_issue_4362:L123](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L123) `eq.is_Pow and eq.as_numer_denom() == (1, dpos ** 2)`
- [test_issue_4362:L125](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L125) `eq.is_Pow and eq.as_numer_denom() == (1, dneg ** 2)`
- [test_issue_4362:L127](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L127) `eq.is_Pow and eq.as_numer_denom() == (dpos ** 2, 1)`
- [test_issue_4362:L129](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L129) `eq.is_Pow and eq.as_numer_denom() == (dneg ** 2, 1)`
- [test_issue_4362:L131](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L131) `eq.is_Pow and eq.as_numer_denom() == (dpos ** 2, 1)`
- [test_issue_4362:L133](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L133) `eq.is_Pow and eq.as_numer_denom() == (dneg ** 2, 1)`
- [test_issue_4362:L137](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L137) `eq.is_Pow and eq.as_numer_denom() == (npos ** pow, dpos ** pow)`
- [test_issue_4362:L141](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L141) `not eq.is_Pow or eq.as_numer_denom() == (nneg ** pow, dpos ** pow)`
- [test_issue_4362:L143](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L143) `eq.is_Pow and eq.as_numer_denom() == ((-nneg) ** pow, (-dneg) ** pow)`
- [test_issue_4362:L145](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L145) `eq.is_Pow and eq.as_numer_denom() == (dpos ** pow, npos ** pow)`
- [test_issue_4362:L149](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L149) `not eq.is_Pow or eq.as_numer_denom() == (dpos ** pow, nneg ** pow)`
- [test_issue_4362:L151](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L151) `eq.is_Pow and eq.as_numer_denom() == ((-dneg) ** pow, (-nneg) ** pow)`
- [test_issue_4362:L155](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L155) `eq.is_Pow and eq.as_numer_denom() == (npos ** pow, dpos ** pow)`
- [test_issue_4362:L157](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L157) `eq.is_Pow and eq.as_numer_denom() == ((-npos) ** pow, (-dneg) ** pow)`
- [test_issue_4362:L159](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L159) `eq.is_Pow and eq.as_numer_denom() == (nneg ** pow, dpos ** pow)`
- [test_issue_4362:L161](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L161) `eq.is_Pow and eq.as_numer_denom() == ((-nneg) ** pow, (-dneg) ** pow)`
- [test_issue_4362:L165](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L165) `eq.is_Pow and eq.as_numer_denom() == ((-dneg) ** pow, (-npos) ** pow)`
- [test_issue_4362:L167](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L167) `eq.is_Pow and eq.as_numer_denom() == (dpos ** pow, nneg ** pow)`
- [test_issue_4362:L169](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L169) `eq.is_Pow and eq.as_numer_denom() == ((-dneg) ** pow, (-nneg) ** pow)`

**a structure query (as_numer_denom)** (16)

- [test_issue_4362:L101](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L101) `num == sqrt(-1)`
- [test_issue_4362:L102](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L102) `den == sqrt(-neg)`
- [test_issue_4362:L104](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L104) `num == 1`
- [test_issue_4362:L105](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L105) `den == sqrt(nonneg)`
- [test_issue_4362:L107](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L107) `num == sqrt(1 / any)`
- [test_issue_4362:L108](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L108) `den == 1`
- [test_issue_4362:L163](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L163) `eq.as_numer_denom() == (dpos ** pow, npos ** pow)`
- [test_issue_4362:L171](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L171) `((1 / (1 + x / 3)) ** (-S.One)).as_numer_denom() == (3 + x, 3)`
- [test_issue_4362:L174](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L174) `(b ** (-y)).as_numer_denom() == (1, b ** y)`
- [test_issue_4362:L175](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L175) `(b ** (-S.One)).as_numer_denom() == ((notp + x) ** 2, notp ** 2)`
- [test_issue_4362:L177](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L177-L178) `(((1 + x / nonp) ** (-2)) ** (-S.One)).as_numer_denom() == ((-nonp - x) ** 2, nonp ** 2)`
- [test_issue_4362:L181](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L181) `(x ** n).as_numer_denom() == (1, x ** (-n))`
- [test_issue_4362:L182](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L182) `sqrt(1 / n).as_numer_denom() == (S.ImaginaryUnit, sqrt(-n))`
- [test_issue_4362:L189](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L189) `(1 / sqrt(x / n)).as_numer_denom() == (sqrt(-n), sqrt(-x))`
- [test_issue_4362:L192](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L192) `e.as_numer_denom() == (e, 1)`
- [test_issue_4362:L194](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L194) `((1 + x / y) ** i).as_numer_denom() == ((x + y) ** i, y ** i)`

**compares with a Python str** (10)

- [test_issue_2993:L499](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L499) `str((2.3 * x - 4) ** 0.3) == '(2.3*x - 4)**0.3'`
- [test_issue_2993:L500](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L500) `str((2.3 * x + 4) ** 0.3) == '(2.3*x + 4)**0.3'`
- [test_issue_2993:L501](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L501) `str((-2.3 * x + 4) ** 0.3) == '(4 - 2.3*x)**0.3'`
- [test_issue_2993:L502](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L502) `str((-2.3 * x - 4) ** 0.3) == '(-2.3*x - 4)**0.3'`
- [test_issue_2993:L503](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L503) `str((2.3 * x - 2) ** 0.3) == '(2.3*x - 2)**0.3'`
- [test_issue_2993:L504](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L504) `str((-2.3 * x - 2) ** 0.3) == '(-2.3*x - 2)**0.3'`
- [test_issue_2993:L505](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L505) `str((-2.3 * x + 2) ** 0.3) == '(2 - 2.3*x)**0.3'`
- [test_issue_2993:L506](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L506) `str((2.3 * x + 2) ** 0.3) == '(2.3*x + 2)**0.3'`
- [test_issue_2993:L507](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L507) `str((2.3 * x - 4) ** Rational(1, 3)) == '(2.3*x - 4)**(1/3)'`
- [test_issue_2993:L509](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L509) `str(eq ** 2) == '(2.3*x + 4)**2'`

**a structure query (as_base_exp)** (8)

- [test_zero:L264](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L264) `(0 ** (2 - x)).as_base_exp() == (0, 2 - x)`
- [test_pow_as_base_exp:L279](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L279) `(S.Infinity ** (2 - x)).as_base_exp() == (S.Infinity, 2 - x)`
- [test_pow_as_base_exp:L280](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L280) `(S.Infinity ** (x - 2)).as_base_exp() == (S.Infinity, x - 2)`
- [test_pow_as_base_exp:L286](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L286) `p.as_base_exp() == (S(2) / 3, x)`
- [test_pow_as_base_exp:L289](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L289) `Pow(1, 2, evaluate=False).as_base_exp() == (S.One, S(2))`
- [test_issue_6208:L334](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L334) `root((6 * I) ** (2 * I), 3).as_base_exp()[1] == Rational(1, 3)`
- [test_issue_6208:L335](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L335) `root((6 * I) ** (I / 3), 3).as_base_exp()[1] == I / 9`
- [test_issue_23918:L654](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L654) `(b ** x).as_base_exp() == (b, x)`

**an assumption query (is_extended_negative)** (6)

- [test_issue_14815:L552](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L552) `sqrt(x).is_extended_negative is False`
- [test_issue_14815:L554](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L554) `sqrt(x).is_extended_negative is None`
- [test_issue_14815:L556](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L556) `sqrt(x).is_extended_negative is False`
- [test_issue_14815:L558](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L558) `sqrt(x).is_extended_negative is False`
- [test_issue_14815:L559](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L559) `sqrt(zoo, evaluate=False).is_extended_negative is False`
- [test_issue_14815:L560](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L560) `sqrt(nan, evaluate=False).is_extended_negative is None`

**an assumption query (is_extended_real)** (6)

- [test_issue_26546:L659](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L659) `x.is_extended_real is True`
- [test_issue_26546:L660](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L660) `sqrt(x + I).is_extended_real is False`
- [test_issue_26546:L661](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L661) `Pow(x + I, S.Half).is_extended_real is False`
- [test_issue_26546:L662](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L662) `Pow(x + I, Rational(1, 2)).is_extended_real is False`
- [test_issue_26546:L663](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L663) `Pow(x + I, Rational(1, 13)).is_extended_real is False`
- [test_issue_26546:L664](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L664) `Pow(x + I, Rational(2, 3)).is_extended_real is None`

**an assumption query (is_real)** (4)

- [test_issue_17450:L539](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L539) `(erf(cosh(1) ** 7) ** I).is_real is None`
- [test_issue_17450:L541](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L541) `Pow(exp(1 + sqrt(2)), (1 - sqrt(2)) * I * pi, evaluate=False).is_real is None`
- [test_issue_17450:L542](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L542) `((-10) ** (10 * I * pi / 3)).is_real is False`
- [test_issue_17450:L543](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L543) `((-5) ** (4 * I * pi)).is_real is False`

**a structure query (args)** (3)

- [test_better_sqrt:L481](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L481) `a.args == (1 / d, n)`
- [test_better_sqrt:L483](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L483) `eq.args == (a, S.Half)`
- [test_issue_2993:L510](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L510) `(1 / eq).args == (eq, -1)`

**a structure query (base)** (3)

- [test_pow_as_base_exp:L282](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L282) `p.base`
- [test_pow_as_base_exp:L284](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L284) `p.base`
- [test_pow_as_base_exp:L287](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L287) `p.base`

**a structure query (exp)** (2)

- [test_issue_6208:L339](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L339) `root(exp(5 * I), 3).exp == Rational(1, 3)`
- [test_issue_7638:L386](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L386) `(((1 + I) ** (I * (1 + 7 * f))) ** Rational(1, 3)).exp == Rational(1, 3)`

**an assumption query (is_positive)** (2)

- [test_issue_8650:L426](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L426) `(n ** n).is_positive is True`
- [test_issue_8650:L428](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L428) `(x ** (5 * (n + 1))).is_positive is True`

**an inequality (a truth value)** (2)

- [test_negative_real:L48](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L48) `feq(S.One / Float(-0.5), -Integer(2))`
- [test_issue_4362:L116](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L116) `dpos > 0 and dneg < 0 and (npos > 0) and (nneg < 0)`

**a conversion to a Python number** (1)

- [test_issue_2993:L513](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L513) `int((q ** 2).subs(x, 1)) == 1`

**a numerical comparison (all_close)** (1)

- [test_issue_25165:L670](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L670) `all_close(e1, e2)`

**a structure query (args), a structure query (len)** (1)

- [test_issue_18762:L578](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L578) `len(g0.series(e, 1, 3).args) == 4`

**a structure query (atoms), a structure query (len)** (1)

- [test_issue_2993:L516](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L516) `len(sqrt(x / (x + y) ** 2 + Float('0.008', 30)).subs(y, pi.n(25)).atoms(Float)) == 2`

**a structure query (func)** (1)

- [test_issue_6100_12942_4473:L328](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L328) `((x * y) ** 1.0).func is Pow`

**an assumption query (is_imaginary)** (1)

- [test_issue_17450:L540](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L540) `(erf(cosh(1) ** 7) ** I).is_imaginary is False`

**compares with a Python bool** (1)

- [test_issue_6100_12942_4473:L318](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L318) `x is not True`

**printing (NS)** (1)

- [test_issue_7638:L393](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L393) `NS(((0.2 + 0.7 * I) ** (0.7 + 1.0 * I)) ** (0.5 - 0.1 * I), 1) == '0.4 + 0.2*I'`

## Not run: 9

**not a chain of == and != (an and/or, an in, a call)** (5)

- [test_issue_4362:L139](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L139) `eq.is_Pow is False and eq.as_numer_denom() == ((-npos) ** pow, (-dneg) ** pow)`
- [test_issue_4362:L147](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L147) `eq.is_Pow is False and eq.as_numer_denom() == (-(-npos) ** pow * (-dneg) ** pow, npos)`
- [test_power_rewrite_exp:L255](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L255-L256) `all(((1 / func(x)).rewrite(exp) == 1 / func(x).rewrite(exp) for func in (sin, cos, tan, sec, csc, sinh, cosh, tanh)))`
- [test_issue_7638:L398](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L398-L399) `sqrt((cos(1) ** 2 + sin(1) ** 2 - 1) ** (3 + I)).exp in [S.Half, Rational(3, 2) + I / 2]`
- [test_issue_14704:L611](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L611) `x == 1 and xexact is False`

**SymPy, given nary's form of the two sides, does not make the test pass** (2)

- [test_better_sqrt:L490](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L490) `sqrt(2 * 9 * I) == Mul(3, 1 + I, evaluate=False)`, in nary `Pow(Mul(18, I), Pow(2, -1)) == Mul(3, Add(1, I))`
- [test_better_sqrt:L493](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L493) `sqrt(-I / 2) == Mul(S.Half, 1 - I, evaluate=False)`, in nary `Pow(Mul(Mul(-1, I), Pow(2, -1)), Pow(2, -1)) == Mul(Pow(2, -1), Add(1, Mul(-1, I)))`

**not reached: needs exp_is_pow, global_parameters** (2)

- [test_power_rewrite_exp:L249](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L249) `(7 ** x).rewrite(exp) == Pow(S.Exp1, x * log(7), evaluate=False)`
- [test_power_rewrite_exp:L251](https://github.com/sympy/sympy/blob/16fa855354eb7bcabd3fe10993841e03b1382692/sympy/core/tests/test_power.py#L251) `(7 ** x).rewrite(exp) == exp(x * log(7), evaluate=False)`
