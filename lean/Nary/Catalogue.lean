/-
Proofs of some of the catalogue's statements, written by hand.

The statements are generated from `catalogue/entries.py` into
`Nary/Catalogue/Statements.lean` as `Statement.add_zero` and so on. Each
theorem here proves one of them under the same name; `catalogue.lean.proved()`
in Python lists them by reading this file. Only cheap proofs are here: most
statements are stated and not proved. A statement without a proof is not a
claim that it is false; the numerical check in `catalogue/numeric.py` is what
every entry passes.
-/
import Nary.Catalogue.Statements
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Deriv

namespace Nary.Catalogue

/-! ### Helpers -/

private theorem holds_ne_zero {z : ℂ} (h : Holds (Ne (some z) (lit 0))) : z ≠ 0 := by
  simpa [Ne, Holds, lit] using h

private theorem holds_gt_zero {z : ℂ} (h : Holds (Gt (some z) (lit 0))) : z ≠ 0 := by
  rintro rfl; simp [Gt, Lt, Holds, lit] at h

private theorem and_two (p q : Prop) : And [some p, some q] = some (p ∧ q) := by
  by_cases hp : p <;> by_cases hq : q <;> simp [And, hp, hq]
  all_goals exact ⟨False, by simp⟩

private theorem or_two (p q : Prop) : Or [some p, some q] = some (p ∨ q) := by
  by_cases hp : p <;> by_cases hq : q <;> simp [Or, hp, hq]
  all_goals exact ⟨True, by simp⟩

/-- `Pow(z, n)` for a positive integer literal `n` is `z ^ n`. -/
private theorem pow_nat (z : ℂ) (n : ℕ) (hn : 0 < n) :
    Pow (some z) (some (n : ℂ)) = some (z ^ n) := by
  by_cases hz : z = 0
  · simp [Pow, withDomain₂, powDomain, powTotal, hz, hn, hn.ne']
  · simp [Pow, withDomain₂, powDomain, powTotal, hz, Complex.exp_nat_mul, Complex.exp_log hz]

private theorem pow_two (z : ℂ) : Pow (some z) (some 2) = some (z ^ 2) := by
  simpa using pow_nat z 2 (by norm_num)

private theorem pow_three (z : ℂ) : Pow (some z) (some 3) = some (z ^ 3) := by
  simpa using pow_nat z 3 (by norm_num)

private theorem pow_five (z : ℂ) : Pow (some z) (some 5) = some (z ^ 5) := by
  simpa using pow_nat z 5 (by norm_num)

private theorem pow_six (z : ℂ) : Pow (some z) (some 6) = some (z ^ 6) := by
  simpa using pow_nat z 6 (by norm_num)

private theorem pow_neg_one (z : ℂ) :
    Pow (some z) (some (-1)) = if z = 0 then none else some z⁻¹ := by
  by_cases hz : z = 0
  · simp [Pow, withDomain₂, powDomain, hz]
  · simp [Pow, withDomain₂, powDomain, hz, powTotal, Complex.exp_neg, Complex.exp_log hz]

/-- `Pow(2, -1)`, the way 1/2 is written. -/
private theorem half_eq : Pow (lit 2) (lit (-1)) = some 2⁻¹ := by
  simpa [lit] using pow_neg_one 2

private theorem pow_four (z : ℂ) : Pow (some z) (some 4) = some (z ^ 4) := by
  simpa using pow_nat z 4 (by norm_num)

private theorem log_exp_one : Complex.log (Complex.exp 1) = 1 :=
  Complex.log_exp (by simp [Real.pi_pos]) (by simp [Real.pi_pos.le])

/-- `Pow(z, w)` for `z ≠ 0`. -/
private theorem pow_ne_zero {z : ℂ} (w : ℂ) (hz : z ≠ 0) :
    Pow (some z) (some w) = some (Complex.exp (w * Complex.log z)) := by
  simp [Pow, withDomain₂, powDomain, powTotal, hz]

/-! ### Entries -/

theorem add_zero : Statement.add_zero := by
  intro x; simp [Add, lit]

theorem mul_one : Statement.mul_one := by
  intro x; simp [Mul, lit]

theorem mul_zero : Statement.mul_zero := by
  intro x; simp [Mul, lit]

theorem sin_mul_zero : Statement.sin_mul_zero := by
  intro x; simp [Mul, sin, lit]

theorem sub_self : Statement.sub_self := by
  intro x; simp [Add, Mul, lit]

theorem add_self : Statement.add_self := by
  intro x; simp [Add, Mul, lit, two_mul]

theorem sub_self_inside : Statement.sub_self_inside := by
  intro x y; simp [Add, Mul, lit]

theorem add_literals : Statement.add_literals := by
  simp [Statement.add_literals, Add, lit]; norm_num

theorem mul_literals : Statement.mul_literals := by
  intro x; simp [Mul, lit]; ring

theorem collect_literal_coefficients : Statement.collect_literal_coefficients := by
  intro x; simp [Add, Mul, lit]; ring

theorem double_negation : Statement.double_negation := by
  intro x; simp [Mul, lit]

theorem commuted_product_cancels : Statement.commuted_product_cancels := by
  intro x y; simp [Add, Mul, lit]; ring

theorem collect_products : Statement.collect_products := by
  intro x y; simp [Add, Mul, lit]; ring

theorem distribute_literal : Statement.distribute_literal := by
  intro x y; simp [Add, Mul, lit]; ring

theorem add_rationals : Statement.add_rationals := by
  simp [Statement.add_rationals, Add, Mul, lit, pow_neg_one]; norm_num

theorem literal_over_itself : Statement.literal_over_itself := by
  simp [Statement.literal_over_itself, Mul, lit, pow_neg_one]

theorem div_self : Statement.div_self := by
  intro x h
  simp [Mul, lit, pow_neg_one, holds_ne_zero h]

theorem div_self_positive : Statement.div_self_positive := by
  intro x h; simp [Mul, lit, pow_neg_one, holds_gt_zero h]

theorem log_mul_zero : Statement.log_mul_zero := by
  intro x h
  simp [Mul, log, withDomain, logDomain, lit, holds_ne_zero h]

theorem expand_square : Statement.expand_square := by
  intro x; simp [Add, Mul, lit, pow_two]; ring

theorem expand_difference_of_squares : Statement.expand_difference_of_squares := by
  intro x y; simp [Add, Mul, lit, pow_two]; ring

theorem expand_product : Statement.expand_product := by
  intro x y z; simp [Add, Mul]; ring

theorem factor_square : Statement.factor_square := by
  intro x; simp [Add, Mul, lit, pow_two]; ring

theorem together : Statement.together := by
  intro x y
  by_cases hx : x = 0 <;> by_cases hy : y = 0 <;>
    simp [Add, Mul, lit, pow_neg_one, hx, hy]
  field_simp
  ring

theorem pow_one : Statement.pow_one := by
  intro x; simpa [lit] using pow_nat x 1 one_pos

theorem pow_zero : Statement.pow_zero := by
  intro x h
  simp [Pow, withDomain₂, powDomain, powTotal, lit, holds_ne_zero h]

theorem mul_self : Statement.mul_self := by
  intro x; simp [Mul, lit, pow_two, sq]

theorem mul_powers_literal : Statement.mul_powers_literal := by
  intro x; simp [Mul, lit, pow_two, pow_three, pow_five]; ring

theorem pow_pow_literal : Statement.pow_pow_literal := by
  intro x; simp [lit, pow_two, pow_three, pow_six]; ring

theorem mul_powers_positive : Statement.mul_powers_positive := by
  intro x a b h
  simp [Mul, Add, pow_ne_zero _ (holds_gt_zero h), ← Complex.exp_add, add_mul]

theorem pow_of_product_literal : Statement.pow_of_product_literal := by
  intro x y; simp [Mul, lit, pow_two, mul_pow]

theorem square_of_sqrt : Statement.square_of_sqrt := by
  intro x
  by_cases hx : x = 0
  · simp only [half_eq]; norm_num [Pow, withDomain₂, powDomain, powTotal, lit, hx]
  · simp [lit, pow_neg_one, pow_ne_zero _ hx, pow_two, ← Complex.exp_nat_mul,
      Complex.exp_log hx]

theorem sqrt_times_sqrt : Statement.sqrt_times_sqrt := by
  intro x
  by_cases hx : x = 0
  · simp only [half_eq]; norm_num [Mul, Pow, withDomain₂, powDomain, powTotal, hx]
  · simp only [half_eq]
    simp [Mul, pow_ne_zero _ hx, ← Complex.exp_add]
    rw [show (2 : ℂ)⁻¹ * Complex.log x + 2⁻¹ * Complex.log x = Complex.log x by ring]
    exact Complex.exp_log hx

theorem i_squared : Statement.i_squared := by
  simp [Statement.i_squared, I, pow_two, lit]

theorem exp_log : Statement.exp_log := by
  intro x h
  have hx := holds_ne_zero h
  simp [exp, log, withDomain, logDomain, hx, Complex.exp_log hx]

theorem exp_two_log : Statement.exp_two_log := by
  intro x h
  have hx := holds_ne_zero h
  simp [exp, log, Mul, withDomain, logDomain, lit, hx, pow_two]
  rw [two_mul, Complex.exp_add, Complex.exp_log hx, sq]

theorem exp_half_log : Statement.exp_half_log := by
  intro x h
  have hx := holds_ne_zero h
  simp [exp, log, Mul, withDomain, logDomain, lit, hx, pow_neg_one, pow_ne_zero _ hx, mul_comm]

theorem exp_add : Statement.exp_add := by
  intro x y; simp [Mul, Add, exp, Complex.exp_add]

theorem exp_squared : Statement.exp_squared := by
  intro x; simp [exp, Mul, lit, pow_two, ← Complex.exp_nat_mul]

theorem exp_zero : Statement.exp_zero := by
  simp [Statement.exp_zero, exp, lit]

theorem exp_one : Statement.exp_one := by
  simp [Statement.exp_one, exp, lit, E]

theorem log_one : Statement.log_one := by
  simp [Statement.log_one, log, withDomain, logDomain, lit]

theorem log_e : Statement.log_e := by
  simp [Statement.log_e, log, withDomain, logDomain, lit, E, Complex.exp_ne_zero, log_exp_one]

theorem e_pow : Statement.e_pow := by
  intro x; simp [Pow, exp, E, withDomain₂, powDomain, powTotal, Complex.exp_ne_zero, log_exp_one]

theorem exp_i_pi : Statement.exp_i_pi := by
  simp [Statement.exp_i_pi, exp, Mul, I, pi, lit, mul_comm Complex.I, Complex.exp_pi_mul_I]

theorem sin_neg : Statement.sin_neg := by
  intro x; simp [sin, Mul, lit]

theorem cos_neg : Statement.cos_neg := by
  intro x; simp [cos, Mul, lit]

theorem tan_neg : Statement.tan_neg := by
  intro x
  by_cases hc : Complex.cos x = 0 <;> simp [tan, withDomain, tanDomain, Mul, lit, hc]

theorem sin_period : Statement.sin_period := by
  intro x; simp [sin, Add, Mul, pi, lit, Complex.sin_add_two_pi]

theorem cos_pi_minus : Statement.cos_pi_minus := by
  intro x; simp [cos, Add, Mul, pi, lit, ← sub_eq_add_neg, Complex.cos_pi_sub]

theorem sin_half_pi_minus : Statement.sin_half_pi_minus := by
  intro x
  simp [sin, cos, Add, Mul, pi, lit, pow_neg_one, ← div_eq_mul_inv, ← sub_eq_add_neg,
    Complex.sin_pi_div_two_sub]

theorem sin_pi : Statement.sin_pi := by
  simp [Statement.sin_pi, sin, pi, lit]

theorem cos_pi : Statement.cos_pi := by
  simp [Statement.cos_pi, cos, pi, lit]

theorem pythagoras : Statement.pythagoras := by
  intro x; simp [Add, sin, cos, pow_two, lit]

theorem pythagoras_inside_sum : Statement.pythagoras_inside_sum := by
  intro x y; simp [Add, sin, cos, pow_two, lit]; ring

theorem one_minus_sin_squared : Statement.one_minus_sin_squared := by
  intro x; simp [Add, Mul, sin, cos, pow_two, lit, Complex.cos_sq']; ring

theorem sin_over_cos : Statement.sin_over_cos := by
  intro x
  by_cases hc : Complex.cos x = 0 <;>
    simp [Mul, sin, cos, tan, withDomain, tanDomain, lit, pow_neg_one, hc, Complex.tan,
      div_eq_mul_inv]

theorem expand_sin_double : Statement.expand_sin_double := by
  intro x; simp [sin, cos, Mul, lit, Complex.sin_two_mul]

theorem sin_double : Statement.sin_double := by
  intro x; simp [sin, cos, Mul, lit, Complex.sin_two_mul]

theorem cos_double : Statement.cos_double := by
  intro x; simp [sin, cos, Add, Mul, lit, pow_two, Complex.cos_two_mul, Complex.cos_sq']; ring

theorem sin4_minus_cos4 : Statement.sin4_minus_cos4 := by
  intro x
  simp [Add, Mul, sin, cos, lit, pow_four, Complex.cos_two_mul, Complex.cos_sq']
  linear_combination (Complex.sin x ^ 2 - Complex.cos x ^ 2 - 1) * Complex.sin_sq_add_cos_sq x

theorem tan_period : Statement.tan_period := by
  intro x
  by_cases hc : Complex.cos x = 0 <;>
    simp [tan, withDomain, tanDomain, Add, pi, Complex.cos_add_pi, hc, Complex.tan_eq_sin_div_cos,
      Complex.sin_add_pi, neg_div_neg_eq]

theorem re_i : Statement.re_i := by
  simp [Statement.re_i, re, I, lit]

theorem re_literal : Statement.re_literal := by
  simp [Statement.re_literal, re, lit]

theorem re_real : Statement.re_real := by
  intro x h; simpa [re, Eq, Holds] using h

theorem eq_self : Statement.eq_self := by
  intro x; simp [Eq, true]

theorem ne_self : Statement.ne_self := by
  intro x; simp [Ne, false]

theorem lt_self_real : Statement.lt_self_real := by
  intro x h
  have h' : (x.re : ℂ) = x := by simpa [re, Eq, Holds] using h
  have : x.im = 0 := by simpa using (congrArg Complex.im h').symm
  simp [Lt, false, this]

theorem lt_literals : Statement.lt_literals := by
  simp [Statement.lt_literals, Lt, true, lit]

theorem not_lt : Statement.not_lt := by
  intro x y
  by_cases h : x.im = 0 ∧ y.im = 0
  · simp [Not, Lt, Ge, Le, h]
  · have h' : ¬(y.im = 0 ∧ x.im = 0) := fun ⟨a, b⟩ => h ⟨b, a⟩
    simp [Not, Lt, Ge, Le, h, h']

theorem not_not : Statement.not_not := by
  intro p; simp [Not]

theorem and_true : Statement.and_true := by
  intro p; simp [and_two, true]

theorem and_false : Statement.and_false := by
  intro p; simp [and_two, false]

theorem or_true : Statement.or_true := by
  intro p; simp [or_two, true]

theorem and_self : Statement.and_self := by
  intro p; simp [and_two]

theorem excluded_middle : Statement.excluded_middle := by
  intro p; simp [or_two, Not, true, em]

theorem contradiction : Statement.contradiction := by
  intro p; simp [and_two, Not, false]

theorem absorption : Statement.absorption := by
  intro p q; simp [and_two, or_two]; tauto

theorem de_morgan : Statement.de_morgan := by
  intro p q; simp [and_two, or_two, Not]; tauto

theorem derivative_sin : Statement.derivative_sin := by
  intro x
  simp [Derivative, apply, sin, cos, (Complex.hasDerivAt_sin x).differentiableAt,
    (Complex.hasDerivAt_sin x).deriv]

theorem call_lambda : Statement.call_lambda := by
  intro x; simp [apply]

theorem call_lambda_literal : Statement.call_lambda_literal := by
  simp [Statement.call_lambda_literal, apply, lit, pow_two]; norm_num

end Nary.Catalogue
