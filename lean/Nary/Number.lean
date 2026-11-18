/-
What a number expression of `python/nary` means.

Functions are partial (issue #2): `1/0` and `log(0)` have no value, and there
is no "undefined" value and no infinity. So a number expression means a
complex number or no value, `Option ℂ`: `some z` is the value `z`, `none` is
no value. Then a rewrite `L → R` that holds everywhere is the plain equation
`L = R`: two such values are equal exactly when both have no value or both
have the same value.

Every function here is strict: if an argument has no value, neither does the
result.

Mathlib's own functions are total and give made-up values outside their
domain (`Complex.log 0 = 0`, `a / 0 = 0`). Those values never reach a result
here: each partial function is `withDomain` (or `withDomain₂`) applied to two
separate pieces, its domain (`logDomain`, ...) and a total function
(`Complex.log`, ...), and gives `none` outside the domain. The domains are
also declared in Python with `domain=`; they are the only part that would
change if they were generated from there.
-/
import Mathlib.Analysis.SpecialFunctions.Complex.Log
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic

noncomputable section
open Classical

namespace Nary

/-- What a `NumberKind` expression means: a complex number, or no value. -/
abbrev Number := Option ℂ

/-- An integer literal, such as `NumberKind(3)` or the `-1` in `x / y`. -/
def lit (n : ℤ) : Number := some (n : ℂ)

/-- The constant `pi`. -/
def pi : Number := some (Real.pi : ℂ)

/-- The constant `E`, the base of the natural logarithm. -/
def E : Number := some (Complex.exp 1)

/-- The constant `I`, the imaginary unit. -/
def I : Number := some Complex.I

/-- `Add(a, b, ...)`: the sum of any number of arguments. `Add()` is 0.
It has a value when every argument has one. (`List.mapM id` turns the list
of arguments into the list of their values, or `none` if one has no value.) -/
def Add (args : List Number) : Number := (args.mapM id).map List.sum

/-- `Mul(a, b, ...)`: the product of any number of arguments. `Mul()` is 1.
It has a value when every argument has one. -/
def Mul (args : List Number) : Number := (args.mapM id).map List.prod

/-- A strict function of one number with a domain: it has a value where its
argument has a value `z` and `domain z` holds, and that value is `f z`.
`f` is a total function (usually Mathlib's); its values outside the domain
are never used. -/
def withDomain (domain : ℂ → Prop) (f : ℂ → ℂ) (a : Number) : Number :=
  a.bind fun z => if domain z then some (f z) else none

/-- The same for a function of two numbers. -/
def withDomain₂ (domain : ℂ → ℂ → Prop) (f : ℂ → ℂ → ℂ) (a b : Number) : Number := do
  let z ← a
  let w ← b
  if domain z w then some (f z w) else none

/-- Where `Pow(base, exp)` has a value: `base ≠ 0` or `re exp > 0`, as
declared with `domain=` in `arithmetic.py`. So `0**0` and `0**(-1)` have
no value. -/
def powDomain (base exponent : ℂ) : Prop := base ≠ 0 ∨ 0 < exponent.re

/-- The power as a total function: `exp(exp * log(base))` with the principal
logarithm, and 0 at base 0. (Inside `powDomain` it agrees with Mathlib's
`base ^ exponent`, which differs only at `0 ^ 0`.) -/
def powTotal (base exponent : ℂ) : ℂ :=
  if base = 0 then 0 else Complex.exp (exponent * Complex.log base)

/-- `Pow(base, exp)`. Has a value where `powDomain` holds. -/
def Pow : Number → Number → Number := withDomain₂ powDomain powTotal

/-- `sin(a)`. Has a value whenever `a` does. -/
def sin (a : Number) : Number := a.map Complex.sin

/-- `cos(a)`. Has a value whenever `a` does. -/
def cos (a : Number) : Number := a.map Complex.cos

/-- Where `tan(a)` has a value: `cos(a) ≠ 0`, as declared with `domain=`
in `elementary.py`. -/
def tanDomain (z : ℂ) : Prop := Complex.cos z ≠ 0

/-- `tan(a)`, which is `sin(a) / cos(a)`. Has a value where `tanDomain`
holds. -/
def tan : Number → Number := withDomain tanDomain Complex.tan

/-- `exp(a)`. Has a value whenever `a` does. -/
def exp (a : Number) : Number := a.map Complex.exp

/-- Where `log(a)` has a value: `a ≠ 0`, as declared with `domain=` in
`elementary.py`. -/
def logDomain (z : ℂ) : Prop := z ≠ 0

/-- `log(a)`, the principal logarithm, whose imaginary part is in `(-π, π]`.
Has a value where `logDomain` holds. -/
def log : Number → Number := withDomain logDomain Complex.log

/-- `re(a)`, the real part of `a`, as a complex number. Has a value whenever
`a` does. -/
def re (a : Number) : Number := a.map fun z => (z.re : ℂ)

end Nary
