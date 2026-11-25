/-
General lemmas for the fixed tactics of `catalogue/lean_tactics.py`.

They are about Nary's meanings, not about any catalogue entry: the
tactics use them to turn an entry's statement into Mathlib's terms. Proofs
of generated entries are never written by hand; these lemmas are, and are
reviewed like any other Lean code here.
-/
import Nary.Number
import Mathlib.Analysis.SpecialFunctions.Pow.Complex

namespace Nary.Catalogue

open Classical in
/-- Inside its domain, `Pow` is Mathlib's complex power `z ^ w`
(`Complex.cpow`, `exp (log z * w)` with the principal logarithm). -/
theorem pow_some_eq_cpow (z w : ℂ) :
    Nary.Pow (some z) (some w) = if Nary.powDomain z w then some (z ^ w) else none := by
  unfold Nary.Pow Nary.withDomain₂ Nary.powTotal
  by_cases h : Nary.powDomain z w
  · have : ¬ (z = 0 ∧ w = 0) := by
      rintro ⟨rfl, rfl⟩; simp [Nary.powDomain] at h
    by_cases hz : z = 0
    · have hw : w ≠ 0 := fun hw => this ⟨hz, hw⟩
      simp [hz, Complex.zero_cpow hw]
    · simp [h, hz, Complex.cpow_def_of_ne_zero hz, mul_comm]
  · simp [h]

end Nary.Catalogue
