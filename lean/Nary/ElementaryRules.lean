import Nary.Literals
import Nary.ElementaryRules.Statements
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Deriv
import Mathlib.Analysis.SpecialFunctions.ExpDeriv

namespace Nary.ElementaryRules

private theorem square (z : ℂ) : Pow (some z) (some 2) = some (z ^ 2) := by
  simpa [lit] using Literals.pow_integer z 2 (Or.inr (by norm_num))

theorem sin_zero : Statement.sin_zero := by simp [Statement.sin_zero, sin, lit]

theorem cos_zero : Statement.cos_zero := by simp [Statement.cos_zero, cos, lit]

theorem tan_zero : Statement.tan_zero := by
  simp [Statement.tan_zero, tan, withDomain, tanDomain, lit]

theorem pythagoras : Statement.pythagoras := by
  intro a h
  obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [sin, cos, square, Add, lit, Complex.sin_sq_add_cos_sq]

theorem pythagoras_scaled : Statement.pythagoras_scaled := by
  intro b a h
  obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h
  cases b <;> simp [sin, cos, lit, square, Add, Mul, ← mul_add, Complex.sin_sq_add_cos_sq]

theorem one_minus_sin_squared : Statement.one_minus_sin_squared := by
  intro a
  cases a with
  | none => simp [sin, cos, Pow, withDomain₂, Add, Mul]
  | some z =>
    simp [sin, cos, square, Add, Mul, lit, Complex.cos_sq', sub_eq_add_neg]

theorem one_minus_cos_squared : Statement.one_minus_cos_squared := by
  intro a
  cases a with
  | none => simp [sin, cos, Pow, withDomain₂, Add, Mul]
  | some z =>
    simp [sin, cos, square, Add, Mul, lit, Complex.sin_sq, sub_eq_add_neg]

theorem sin_over_cos : Statement.sin_over_cos := by
  intro a
  cases a with
  | none => simp [sin, cos, tan, withDomain, Pow, withDomain₂, Mul]
  | some z =>
    by_cases hz : Complex.cos z = 0
    · simp [sin, cos, tan, withDomain, tanDomain, Pow, withDomain₂, powDomain, Mul, lit, hz]
      norm_num
    · rw [cos, Option.map_some, Literals.pow_integer _ _ (Or.inl hz)]
      simp [sin, tan, withDomain, tanDomain, Mul, hz, Complex.tan_eq_sin_div_cos, div_eq_mul_inv]

theorem re_real : Statement.re_real := by
  intro a h
  cases a with
  | none => rfl
  | some z => simpa [Eq, re, Holds] using h

theorem re_pi : Statement.re_pi := by simp [Statement.re_pi, re, pi]

theorem re_e : Statement.re_e := by
  simp only [Statement.re_e, re, E, Option.map_some]
  rw [← Complex.ofReal_one, ← Complex.ofReal_exp, Complex.ofReal_re]

theorem re_i : Statement.re_i := by simp [Statement.re_i, re, I, lit]

theorem re_re : Statement.re_re := by
  intro a; cases a <;> simp [re]

theorem derivative_sin : Statement.derivative_sin := by
  funext z
  simp [Derivative, sin, cos, Complex.differentiableAt_sin, Complex.deriv_sin]

theorem derivative_exp : Statement.derivative_exp := by
  funext z
  simp [Derivative, exp, Complex.differentiableAt_exp, Complex.deriv_exp]

private theorem inverse (n : ℤ) (h : n ≠ 0) : Pow (lit n) (lit (-1)) = some ((n : ℂ)⁻¹) := by
  rw [lit, Literals.pow_integer _ _ (Or.inl (by exact_mod_cast h))]
  simp

theorem sin_pi_6 : Statement.sin_pi_6 := by
  simp only [Statement.sin_pi_6]
  rw [inverse 6 (by norm_num), inverse 2 (by norm_num)]
  have : Complex.sin (Real.pi * 6⁻¹) = 2⁻¹ := by
    rw [show (Real.pi : ℂ) * 6⁻¹ = ((Real.pi / 6 : ℝ) : ℂ) by push_cast; ring,
      ← Complex.ofReal_sin, Real.sin_pi_div_six]
    push_cast; ring
  simp [sin, Mul, pi, this]

theorem cos_pi_3 : Statement.cos_pi_3 := by
  simp only [Statement.cos_pi_3]
  rw [inverse 3 (by norm_num), inverse 2 (by norm_num)]
  have : Complex.cos (Real.pi * 3⁻¹) = 2⁻¹ := by
    rw [show (Real.pi : ℂ) * 3⁻¹ = ((Real.pi / 3 : ℝ) : ℂ) by push_cast; ring,
      ← Complex.ofReal_cos, Real.cos_pi_div_three]
    push_cast; ring
  simp [cos, Mul, pi, this]

theorem tan_pi_4 : Statement.tan_pi_4 := by
  simp only [Statement.tan_pi_4]
  rw [inverse 4 (by norm_num)]
  have h : (Real.pi : ℂ) * 4⁻¹ = ((Real.pi / 4 : ℝ) : ℂ) := by push_cast; ring
  have hc : Complex.cos (Real.pi * 4⁻¹) ≠ 0 := by
    rw [h, ← Complex.ofReal_cos]
    exact_mod_cast (Real.cos_pos_of_mem_Ioo ⟨by linarith [Real.pi_pos], by linarith [Real.pi_pos]⟩).ne'
  have ht : Complex.tan (Real.pi * 4⁻¹) = 1 := by
    rw [h, ← Complex.ofReal_tan, Real.tan_pi_div_four]; simp
  simp [tan, withDomain, tanDomain, Mul, pi, hc, ht, lit]

private theorem root (n : ℤ) (hn : 0 < n) :
    Pow (lit n) (Pow (lit 2) (lit (-1))) = some ((Real.sqrt n : ℝ) : ℂ) := by
  rw [inverse 2 (by norm_num)]
  have hn' : (n : ℂ) ≠ 0 := by exact_mod_cast hn.ne'
  have hr : (0 : ℝ) < n := by exact_mod_cast hn
  have hs : Real.sqrt n = Real.exp (2⁻¹ * Real.log n) := by
    rw [← Real.sqrt_sq (Real.exp_pos _).le, sq, ← Real.exp_add,
      show 2⁻¹ * Real.log n + 2⁻¹ * Real.log n = Real.log n by ring, Real.exp_log hr]
  have : Complex.exp (2⁻¹ * Complex.log (n : ℂ)) = ((Real.sqrt n : ℝ) : ℂ) := by
    rw [hs, show ((n : ℂ)) = ((n : ℝ) : ℂ) by push_cast; rfl, ← Complex.ofReal_log hr.le,
      Complex.ofReal_exp]
    push_cast; rfl
  simp [lit, Pow, withDomain₂, powDomain, powTotal, hn', this]

theorem sin_pi_4 : Statement.sin_pi_4 := by
  simp only [Statement.sin_pi_4]
  rw [inverse 4 (by norm_num), root 2 (by norm_num), inverse 2 (by norm_num)]
  have : Complex.sin (Real.pi * 4⁻¹) = 2⁻¹ * ((Real.sqrt 2 : ℝ) : ℂ) := by
    rw [show (Real.pi : ℂ) * 4⁻¹ = ((Real.pi / 4 : ℝ) : ℂ) by push_cast; ring,
      ← Complex.ofReal_sin, Real.sin_pi_div_four]
    push_cast; ring
  simp [sin, Mul, pi, this]

theorem cos_pi_4 : Statement.cos_pi_4 := by
  simp only [Statement.cos_pi_4]
  rw [inverse 4 (by norm_num), root 2 (by norm_num), inverse 2 (by norm_num)]
  have : Complex.cos (Real.pi * 4⁻¹) = 2⁻¹ * ((Real.sqrt 2 : ℝ) : ℂ) := by
    rw [show (Real.pi : ℂ) * 4⁻¹ = ((Real.pi / 4 : ℝ) : ℂ) by push_cast; ring,
      ← Complex.ofReal_cos, Real.cos_pi_div_four]
    push_cast; ring
  simp [cos, Mul, pi, this]

theorem cos_pi_6 : Statement.cos_pi_6 := by
  simp only [Statement.cos_pi_6]
  rw [inverse 6 (by norm_num), root 3 (by norm_num), inverse 2 (by norm_num)]
  have : Complex.cos (Real.pi * 6⁻¹) = 2⁻¹ * ((Real.sqrt 3 : ℝ) : ℂ) := by
    rw [show (Real.pi : ℂ) * 6⁻¹ = ((Real.pi / 6 : ℝ) : ℂ) by push_cast; ring,
      ← Complex.ofReal_cos, Real.cos_pi_div_six]
    push_cast; ring
  simp [cos, Mul, pi, this]

theorem sin_pi_3 : Statement.sin_pi_3 := by
  simp only [Statement.sin_pi_3]
  rw [inverse 3 (by norm_num), root 3 (by norm_num), inverse 2 (by norm_num)]
  have : Complex.sin (Real.pi * 3⁻¹) = 2⁻¹ * ((Real.sqrt 3 : ℝ) : ℂ) := by
    rw [show (Real.pi : ℂ) * 3⁻¹ = ((Real.pi / 3 : ℝ) : ℂ) by push_cast; ring,
      ← Complex.ofReal_sin, Real.sin_pi_div_three]
    push_cast; ring
  simp [sin, Mul, pi, this]

end Nary.ElementaryRules
