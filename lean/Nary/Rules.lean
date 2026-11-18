/-
Issue #2's three kinds of rewrite rule, proved from the definitions. Each
is a check that the definitions can be used; they are not a library of rules.
-/
import Nary.Logic

namespace Nary

/-- Ungated: `a + 0 → a`, for every `a`, including an `a` with no value. -/
theorem add_zero (a : Number) : Add [a, lit 0] = a := by
  cases a <;> simp [Add, lit]

/-- Gated on an erased subexpression having a value: `0 * a → 0` whenever
`a` has one. -/
theorem zero_mul (a : Number) (h : a ≠ none) : Mul [lit 0, a] = lit 0 := by
  cases a with
  | none => exact absurd rfl h
  | some x => simp [Mul, lit]

/-- Without that condition `0 * a → 0` is wrong: at `a = log(0)` the left
side has no value and the right side is 0. -/
example : Mul [lit 0, log (lit 0)] ≠ lit 0 := by simp [Mul, log, withDomain, logDomain, lit]

/-- Gated on a value: `a / a → 1` when `a ≠ 0`, with `a / a` spelled as
Python builds it, `Mul(a, Pow(a, -1))`. The condition is the boolean
expression `Ne(a, 0)`; it holds only when `a` has a value, and that value is
not 0. -/
theorem div_self (a : Number) (h : Holds (Ne a (lit 0))) :
    Mul [a, Pow a (lit (-1))] = lit 1 := by
  cases a with
  | none => simp [Ne, Holds] at h
  | some x =>
    have hx : x ≠ 0 := by simpa [Ne, Holds, lit] using h
    have : x * Complex.exp (-Complex.log x) = 1 := by
      rw [Complex.exp_neg, Complex.exp_log hx, mul_inv_cancel₀ hx]
    simp [Mul, Pow, withDomain₂, powDomain, powTotal, lit, hx, this]

end Nary
