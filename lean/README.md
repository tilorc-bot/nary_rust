# Lean definitions

What the functions declared in `python/nary/` mean, written as Lean 4
definitions with [Mathlib](https://github.com/leanprover-community/mathlib4),
so that rewrite rules can later be proved correct. This directory touches no
Python and no Rust. The meaning follows issue #2.

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
domains are the same conditions that `python/nary/` records with
`set_domain`, kept apart so that they could later be generated from there.

## Files

| File | What it is |
|---|---|
| `Nary/Number.lean` | Integer literals, the constants, `Add`, `Mul`, `Pow` and the elementary functions. |
| `Nary/Logic.lean` | Comparisons, `And`, `Or`, `Not`, `true`, `false`, and `Holds` (a condition has a value and it is true). |
| `Nary/Calculus.lean` | Applying a function to an argument, and `Derivative`. |
| `Nary/Rules.lean` | Issue #2's three kinds of rule, proved: `a + 0 → a`, `0 * a → 0` when `a` has a value, `a / a → 1` when `a ≠ 0`. |

## Build

Needs [elan](https://github.com/leanprover/elan), which installs the Lean
version named in `lean-toolchain`. In this directory:

    lake exe cache get
    lake build

The first command downloads Mathlib's compiled files (a few GB), so Mathlib
is not compiled from source; `lake build` then takes under a minute.

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

The domains of `Pow`, `tan` and `log` are the ones recorded with
`set_domain` in `python/nary/`.

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
