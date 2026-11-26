import Mathlib.Analysis.SpecialFunctions.Pow.Complex
import Nary.Logic

namespace Nary.Literals

private theorem mapM_some (zs : List ℂ) : (zs.map some).mapM id = some zs := by
  induction zs with
  | nil => rfl
  | cons z zs ih => simp [List.mapM_cons, ih]

theorem add_values (zs : List ℂ) : Add (zs.map some) = some zs.sum := by
  rw [Add, mapM_some]; rfl

theorem mul_values (zs : List ℂ) : Mul (zs.map some) = some zs.prod := by
  rw [Mul, mapM_some]; rfl

theorem pow_integer (z : ℂ) (n : ℤ) (h : z ≠ 0 ∨ 0 < n) :
    Pow (some z) (lit n) = some (z ^ n) := by
  by_cases hz : z = 0
  · have hn : 0 < n := h.resolve_left (not_not.mpr hz)
    simp [Pow, withDomain₂, powDomain, powTotal, lit, hz, hn, zero_zpow n hn.ne']
  · rw [← Complex.cpow_intCast, Complex.cpow_def_of_ne_zero hz, mul_comm]
    simp [Pow, withDomain₂, powDomain, powTotal, lit, hz]

theorem i_mul_i : Mul [I, I] = lit (-1) := by
  simp [Mul, I, lit]

theorem eq_values (z w : ℂ) : Eq (some z) (some w) = some (z = w) := rfl

theorem ne_values (z w : ℂ) : Ne (some z) (some w) = some (z ≠ w) := rfl

theorem lt_real (x y : ℝ) : Lt (some x) (some y) = some (x < y) := by
  simp [Lt]

theorem le_real (x y : ℝ) : Le (some x) (some y) = some (x ≤ y) := by
  simp [Le]

theorem lt_not_real (z w : ℂ) (h : z.im ≠ 0 ∨ w.im ≠ 0) : Lt (some z) (some w) = none := by
  simp [Lt]; tauto

theorem le_not_real (z w : ℂ) (h : z.im ≠ 0 ∨ w.im ≠ 0) : Le (some z) (some w) = none := by
  simp [Le]; tauto

end Nary.Literals
