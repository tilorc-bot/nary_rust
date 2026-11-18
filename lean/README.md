# Lean definitions

What the functions declared in `python/nary/` mean, written as Lean 4
definitions with [Mathlib](https://github.com/leanprover-community/mathlib4),
and proofs that the rewrite rules of `python/nary/arithmetic_rules.py` are
correct, with each rule's Lean statement printed from the Python rule (see
"Rules and facts, proved" below). The meaning follows issue #2.

Each declared function is a Lean definition on values; there is no Lean type
of expressions yet. Functions are partial, so:

- a number expression (`NumberKind`) means a complex number or no value,
  `Option ℂ` (named `Number` here): `some z` is the value `z`, `none` is no
  value;
- a boolean expression (`BoolKind`) means a proposition or no value,
  `Option Prop` (named `Boolean`);
- a function of one number (`FunctionKind((NumberKind,), NumberKind)`) means
  a function from complex numbers to a complex number or no value,
  `ℂ → Option ℂ` (named `NumberFunction`).

A rewrite `L → R` is sound where a condition holds if, there, both sides
have no value or both have the same value. With these meanings that is the
plain equation `L = R`, assumed only where the condition holds.

Every function is strict (if an argument has no value, so does the result),
except `And` and `Or`. Mathlib's own functions give made-up values outside
their domain (`Complex.log 0 = 0`, `a / 0 = 0`), so those values must never
appear in a result. Each partial function is therefore written as a wrapper,
`withDomain` (or `withDomain₂` for two arguments), applied to two separate
named pieces: its domain, the condition under which it has a value
(`logDomain`, `tanDomain`, `powDomain`), and a total function (`Complex.log`,
`Complex.tan`, `powTotal`). Outside the domain the result is no value. The
domains are the same conditions that `python/nary/` declares with
`domain=`, kept apart so that they could later be generated from there.

## Files

| File | What it is |
|---|---|
| `Nary/Number.lean` | Integer literals, the constants, `Add`, `Mul`, `Pow` and the elementary functions. |
| `Nary/Logic.lean` | Comparisons, `And`, `Or`, `Not`, `true`, `false`, and `Holds` (a condition has a value and it is true). |
| `Nary/Calculus.lean` | Applying a function to an argument, and `Derivative`. |
| `Nary/Facts.lean` | What the facts `unordered` and `flat` mean, `Unordered` and `Flat`, for a function on a list. |
| `Nary/ArithmeticRules/Statements.lean` | Generated, do not edit: the statements of the rules and facts of `arithmetic_rules.py`, and the structure `Proved` that lists them. |
| `Nary/ArithmeticRules.lean` | The proofs of those statements, written by hand. |
| `generate_rules.py` | Writes `Nary/ArithmeticRules/Statements.lean` from Python; see below. |
| `check_printer.py` | Checks with Lean that what `nary.lean` prints is accepted; see below. |

## Build

Needs [elan](https://github.com/leanprover/elan), which installs the Lean
version named in `lean-toolchain`. In this directory:

    lake exe cache get
    lake build

The first command downloads Mathlib's compiled files (a few GB), so Mathlib
is not compiled from source; `lake build` then takes under a minute.

## Printing expressions from Python

`python/nary/lean.py` (imported as `nary.lean`) writes an `nary` expression
as the Lean term built from these definitions. `to_lean(e)` returns the
term; `to_lean_example(e)` returns a line that Lean checks on its own, with
the free symbols as variables:

    >>> from nary import NumberKind, sin
    >>> from nary.calculus import Derivative
    >>> from nary.lean import to_lean, to_lean_example
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> to_lean(Derivative(sin)(x ** 2))
    'Nary.apply (Nary.Derivative (fun z => Nary.sin (some z))) (Nary.Pow (some x) (Nary.lit 2))'
    >>> print(to_lean_example(x - y))
    noncomputable example (x y : ℂ) : Nary.Number := Nary.Add [some x, Nary.Mul [Nary.lit (-1), some y]]

The names are always the full ones (`Nary.Add`, `Nary.Eq`, `Nary.true`), so
the output means the same inside or outside `namespace Nary` and after
`open Nary`. A `NumberKind` symbol `x` is a variable `x : ℂ` and prints as
`some x`, a `BoolKind` symbol `p : Prop` prints as `some p`, and a
`FunctionKind((NumberKind,), NumberKind)` symbol is `f : ℂ → Nary.Number`.
`f(a)`, and any other call whose head is not a declared function, prints as
`Nary.apply f a`; so `Derivative(f)(a)` is `Nary.apply (Nary.Derivative f) a`.
The line from `to_lean_example` starts with `noncomputable`, because these
definitions are noncomputable and Lean would otherwise try to compile the
example. Everything in "Left out" below, lambdas other than one `NumberKind`
variable with a `NumberKind` body, and functions or constants not listed in
`nary.lean.LEAN_NAMES` are refused with a `ValueError`. The module docstring
gives the details.

`check_printer.py` prints about a dozen examples, covering each of these
rules, into a temporary Lean file that imports `Nary`, and runs Lean on it
in this directory, once at the top level, once after `open Nary` and once
inside `namespace Nary`. It reports success, or Lean's errors and the file.
After `lake build`, from the top of the repository, with the Python that
has `nary` installed:

    .venv/bin/python lean/check_printer.py

It needs `lake` on `PATH` or in `~/.elan/bin`. It is run by hand and is not
part of the Python tests, which do not need Lean. Lean checks only that each
line is well typed, not that it means the same as the Python expression.

## Rules and facts, proved

Every rule in `nary.arithmetic_rules.rules`, and the four facts recorded
there (`unordered(Add)`, `flat(Add)`, `unordered(Mul)`, `flat(Mul)`), is
proved in Lean. The statements are not written in Lean by hand: they are
printed from the Python rules, so the rule that the engine applies and the
statement that is proved cannot drift apart unnoticed.

### How a rule becomes a theorem

A rule claims, as `python/nary/rules.py` states: wherever its condition
holds and every erased variable has a value, the pattern and the replacement
both have no value or both have the same value. On `Nary.Number` that is
plain equality, so `nary.lean.to_lean_rule` prints a rule as: for all values
of the variables, `Nary.Holds <condition>` → each erased variable `≠ none` →
`<pattern> = <replacement>`. For
`rule(a / a, 1, when=Ne(a, 0), name="div_self")` it prints

    abbrev div_self : Prop :=
      ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → a ≠ none → Nary.Mul [a, Nary.Pow a (Nary.lit (-1))] = Nary.lit 1

A variable of a rule stands for any expression of its kind, including one
with no value, so a `NumberKind` variable `a` is `a : Nary.Number` and is
printed as `a`; in an ordinary expression a symbol stands for a number with
a value, and `to_lean` prints it as `some a`. A `BoolKind` variable is
`p : Nary.Boolean`. A variable of `FunctionKind((NumberKind,), NumberKind)`
is `f : Nary.NumberFunction` and gets no `≠ none` hypothesis, because an
expression of a function kind always means a function (which may have no
value at some points). `Nary.Holds c` is false where `c` has no value. A
rule without a condition has no `Nary.Holds` hypothesis, and one that erases
no variable has no `≠ none` hypothesis.

A rule may do arithmetic on literals with `computed(...)` in its
replacement, as `rule(m + n, computed(m + n), name="add_literals")` does
(see `python/nary/rules.py`). A variable inside `computed(...)` matches only
an integer literal, so it is an integer, `m : ℤ`, printed as `Nary.lit m`,
and `computed(e)` is printed as `Nary.lit (e)` with `e` in Lean's integer
arithmetic:

    abbrev add_literals : Prop :=
      ∀ (m n : ℤ), Nary.Add [Nary.lit m, Nary.lit n] = Nary.lit (m + n)

The engine works out `m + n` with Python integers. That Python's `+` and `*`
on integers agree with Lean's on `ℤ` is taken on trust.

The name given with `rule(..., name="div_self")` is the name of the
statement, `Nary.ArithmeticRules.Statement.div_self`, and of its theorem,
`Nary.ArithmeticRules.div_self`. The namespace keeps them apart from
Mathlib's `add_zero`, `div_self` and so on. A rule without a name, or whose
name is not a plain identifier, cannot be printed as a theorem.

The facts are printed as `Nary.Unordered Nary.Add`, `Nary.Flat Nary.Add`
and so on (by `nary.lean.to_lean_facts`), with these definitions, written by
hand in `Nary/Facts.lean`:

    def Unordered (f : List α → β) : Prop := ∀ xs ys, xs.Perm ys → f xs = f ys
    def Flat (f : List α → α) : Prop := ∀ xs ys zs, f (xs ++ f ys :: zs) = f (xs ++ ys ++ zs)

They are stated only for a function that takes its arguments as a list;
`to_lean_facts` refuses any other function.

### The files and how to regenerate

- `generate_rules.py` writes `Nary/ArithmeticRules/Statements.lean`. It
  holds one `abbrev Statement.<name> : Prop` for each rule and each fact,
  and a structure `Proved` with one field `<name> : Statement.<name>` for
  each of them. Its first lines say that it is generated and must not be
  edited.
- `Nary/ArithmeticRules.lean`, written by hand, imports it and proves
  `theorem <name> : Statement.<name>` for each one, then ends with
  `theorem proved : Proved`, which lists every theorem by name.

After changing, adding or removing a rule in `arithmetic_rules.py`, from the
top of the repository:

    .venv/bin/python lean/generate_rules.py
    cd lean && lake build

and add or fix proofs in `Nary/ArithmeticRules.lean` until `lake build`
passes. A rule in another list is not covered: the script reads only
`nary.arithmetic_rules.rules` and the facts for `Add` and `Mul`.

### The two checks

1. The Python test `test_generated_lean_file_is_current` in
   `tests/test_lean.py` compares the committed
   `Nary/ArithmeticRules/Statements.lean` with what `generate_rules.py`
   prints now. It fails when a rule changed in Python, or one was added or
   removed, and the script was not run. It does not need Lean.
2. `lake build` fails when a generated statement has no proof: `Proved`
   then has a field that `proved` does not give. It also fails when a
   statement changed and its proof no longer proves it, because each
   theorem's type is the generated statement.

When both pass, each rule and fact as written in Python is proved, from the
definitions here. What is trusted: the printer in `nary.lean` (that the
printed statement says what the Python rule means), the Lean definitions
of the functions, and that Python and Lean agree on `+` and `*` of integers. `#print axioms Nary.ArithmeticRules.proved` shows only
Lean's standard axioms `propext`, `Classical.choice` and `Quot.sound`.

### Why the engine may match part of an `Add` or `Mul`

`nary.rewriting` lets a pattern `Add(p1, ..., pk)` match some of the
arguments of a longer `Add(e1, ..., en)`, puts the replacement `R` where the
first matched argument was, and keeps the others. Call the matched arguments
`m` (in the order the pattern matched them) and the others `r`. By
`Unordered Add`, `Add(e1, ..., en)` has the same value as `Add(m ++ r)`; by
`Flat Add` (with an empty first list), that is `Add(Add(m) :: r)`; the
pattern matched `Add(m)` (its own arguments in any order, by `Unordered`
again), so where the rule's hypotheses hold the proved rule gives
`Add(m) = R`, and the whole is `Add(R :: r)`; by `Unordered`, `R` may stand
at the position of the first matched argument; and by `Flat` again,
merging `R` into the sum when it is itself an `Add`, as the engine does, does
not change the value. Flattening before matching (`Add(Add(x, y), z)` matched
as `Add(x, y, z)`) is `Flat` itself. The same holds for `Mul`. This
argument is on paper: the engine is not proved, only the rules and facts it
uses.

## Python name → Lean definition

All names are in the namespace `Nary`. Some of them (`Eq`, `Ne`, `And`,
`Or`, `Not`, `Pow`, `true`, `false`) are also names in Lean itself, so use
them inside `namespace Nary` or as `Nary.Eq` and so on, not after
`open Nary`, where they are ambiguous. "Has a value when" assumes that
every argument has a value, except for `And` and `Or`.

| Python | Lean | Has a value when |
|---|---|---|
| `NumberKind(n)`, an integer literal | `lit n` | always; it is `n` as a complex number |
| `pi`, `E`, `I` | `pi`, `E`, `I` | always; `E` is `exp(1)` |
| `Add(a, ...)` | `Add [a, ...]` | always; `Add()` is 0 |
| `Mul(a, ...)` | `Mul [a, ...]` | always; `Mul()` is 1 |
| `Pow(base, exp)` | `Pow base exp` | `powDomain`: `base ≠ 0` or `re exp > 0`; the value is `powTotal`, `exp(exp * log(base))`, and 0 at base 0 |
| `sin`, `cos`, `exp`, `re` | `sin`, `cos`, `exp`, `re` | always |
| `tan(a)` | `tan a` | `tanDomain`: `cos(a) ≠ 0` |
| `log(a)` | `log a` | `logDomain`: `a ≠ 0`; the principal logarithm, imaginary part in `(-π, π]` |
| `Eq(a, b)`, `Ne(a, b)` | `Eq a b`, `Ne a b` | always |
| `Lt`, `Le`, `Gt`, `Ge` | `Lt a b`, `Le a b`, `Gt a b`, `Ge a b` | both values are real (not confirmed) |
| `Not(p)` | `Not p` | always |
| `And(p, ...)` | `And [p, ...]` | some argument is false (then false), or every argument has a value (not confirmed); `And()` is true |
| `Or(p, ...)` | `Or [p, ...]` | some argument is true (then true), or every argument has a value (not confirmed); `Or()` is false |
| `true`, `false` | `true`, `false` | always |
| `f(a)`, `f` a function | `apply f a` | `f` has a value at `a` |
| `sin` used as a function | `fun z => sin (some z)` | |
| `Lambda(x, body)` | `fun x => body`, with `x` read as `some x` | |
| `Derivative(f)(a)` | `Derivative f a` | `f` has a value at every point near `a` and is complex-differentiable at `a` |

The domains of `Pow`, `tan` and `log` are the ones declared with
`domain=` in `python/nary/`.

## Choices not confirmed by the owner

Issue #2 does not decide these:

- `Lt`, `Le`, `Gt`, `Ge` have a value only when both sides are real, so
  `I > 0` has no value (issue #2 proposes this).
- `And` and `Or` follow Kleene logic: `false and <no value>` is false,
  `true or <no value>` is true (issue #2 proposes this).
- `Pow` is `exp(exp * log(base))` with the principal logarithm, and 0 at
  base 0 when `re exp > 0`. There is no separate power with a natural-number
  exponent, so `a**0` has no value at `a = 0`.
- `Derivative` is the complex derivative, and needs the function to have a
  value on a whole disc around the point. So `Derivative(re)` has no value
  anywhere, although `re` has a derivative along the real line.
- `Option` is used for "no value", rather than Mathlib's `Part`. `Option`
  is the simpler of the two and gives the same equality; `Part` would only
  be needed if whether something has a value had to stay undecided in the
  definitions, which classical logic makes unnecessary here.

## Left out

These have no definition yet, because the Python declarations do not fix
what they mean:

- `Limit(f, a)`: from which side? Over all complex numbers near `a`, along
  the real line from both sides, or from the right only (SymPy's default
  `dir="+"`)? Does `f` need a value at every point near `a` other than `a`?
- `Sum(f, lower, upper)` and `Product(f, lower, upper)`: is `upper`
  included (it is in SymPy)? What do they mean when the bounds are not
  integers, or when `upper < lower`?
- `Integral(f, lower, upper)`: what is it when the bounds are not real:
  along the straight line between them, or no value? For real bounds, which
  kind of integrability is required for it to have a value (Lebesgue, or the
  improper integral when `f` has no value at a point)? Is it the negative
  when `upper < lower`?
- `Antiderivative(f)`: it is only fixed up to a constant (on each connected
  piece of where `f` has a value). Which one is meant, or should it not
  denote a single function at all?
- The matrices of `matrices.py` (`MatAdd`, `MatMul`, `Transpose`,
  `Inverse`, `Determinant`, `Trace`): a `Matrix` has no shape, so there is
  no type of values to give them. Is a matrix's shape part of its value
  (then adding matrices of different shapes would have no value, and
  `MatAdd()` would need a shape), or will the shape become part of the
  kind? `Inverse` also has no domain recorded yet.
