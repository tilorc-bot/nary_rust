import Nary.Literals
import Nary.ArithmeticRules.Statements

namespace Nary.ArithmeticRules

private theorem holds_ne_zero {a : Number} (h : Holds (Ne a (lit 0))) :
    ∃ z, a = some z ∧ z ≠ 0 := by
  cases a with
  | none => simp [Ne, Holds] at h
  | some z => exact ⟨z, rfl, by simpa [Ne, Holds, lit] using h⟩

theorem add_identity : Statement.add_identity := by
  intro a; cases a <;> simp [Add, lit]

theorem mul_identity : Statement.mul_identity := by
  intro a; cases a <;> simp [Mul, lit]

theorem mul_absorbing : Statement.mul_absorbing := by
  intro a h
  obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [Mul, lit]

example : Mul [log (lit 0), lit 0] ≠ lit 0 := by
  simp [Mul, log, withDomain, logDomain, lit]

theorem add_self : Statement.add_self := by
  intro a; cases a <;> simp [Add, Mul, lit, two_mul]

theorem add_inverse : Statement.add_inverse := by
  intro a h
  obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [Add, Mul, lit]

theorem mul_inverse : Statement.mul_inverse := by
  intro a h _
  obtain ⟨z, rfl, hz⟩ := holds_ne_zero h
  have : z * Complex.exp (-Complex.log z) = 1 := by
    rw [Complex.exp_neg, Complex.exp_log hz, mul_inv_cancel₀ hz]
  simp [Mul, Pow, withDomain₂, powDomain, powTotal, lit, hz, this]

theorem pow_one : Statement.pow_one := by
  intro a
  cases a with
  | none => simp [Pow, withDomain₂]
  | some z =>
    by_cases hz : z = 0
    · simp [Pow, withDomain₂, powDomain, powTotal, lit, hz]
    · simp [Pow, withDomain₂, powDomain, powTotal, lit, hz, Complex.exp_log hz]

theorem pow_zero : Statement.pow_zero := by
  intro a h _
  obtain ⟨z, rfl, hz⟩ := holds_ne_zero h
  simp [Pow, withDomain₂, powDomain, powTotal, lit, hz]

theorem exp_log : Statement.exp_log := by
  intro a h
  obtain ⟨z, rfl, hz⟩ := holds_ne_zero h
  simp [exp, log, withDomain, logDomain, hz, Complex.exp_log hz]

private abbrev values (xs : List Number) : Option (Multiset ℂ) :=
  (xs.mapM id).map (fun l : List ℂ => (l : Multiset ℂ))

private theorem values_cons (x : Number) (l : List Number) :
    values (x :: l) = x.bind (fun a => (values l).map (Multiset.cons a)) := by
  cases x <;> cases h : l.mapM id <;> simp [values, List.mapM_cons, h]

private theorem values_perm {xs ys : List Number} (h : xs.Perm ys) :
    values xs = values ys := by
  induction h with
  | nil => rfl
  | cons x _ ih => rw [values_cons, values_cons, ih]
  | swap x y l =>
    simp only [values_cons]
    cases x <;> cases y <;> cases values l <;> simp [Multiset.cons_swap]
  | trans _ _ ih₁ ih₂ => exact ih₁.trans ih₂

theorem add_unordered : Statement.add_unordered := by
  intro xs ys h
  have := congrArg (Option.map Multiset.sum) (values_perm h)
  simpa [values, Add, Option.map_map, Function.comp_def] using this

theorem mul_unordered : Statement.mul_unordered := by
  intro xs ys h
  have := congrArg (Option.map Multiset.prod) (values_perm h)
  simpa [values, Mul, Option.map_map, Function.comp_def] using this

theorem add_flat : Statement.add_flat := by
  intro xs ys zs
  simp only [Add, List.mapM_append, List.mapM_cons]
  cases xs.mapM id <;> cases ys.mapM id <;> cases zs.mapM id <;> simp

theorem mul_flat : Statement.mul_flat := by
  intro xs ys zs
  simp only [Mul, List.mapM_append, List.mapM_cons]
  cases xs.mapM id <;> cases ys.mapM id <;> cases zs.mapM id <;> simp

private theorem log_exp_real {w : ℂ} (h : w.im = 0) : Complex.log (Complex.exp w) = w :=
  Complex.log_exp (by rw [h]; linarith [Real.pi_pos]) (by rw [h]; exact Real.pi_pos.le)

theorem one_pow : Statement.one_pow := by
  intro a h
  obtain ⟨w, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [Pow, withDomain₂, powDomain, powTotal, lit]

theorem zero_pow : Statement.zero_pow := by
  intro a h _
  cases a with
  | none => simp [Gt, Lt, re, Holds] at h
  | some w =>
    have hw : 0 < w.re := by simpa [Gt, Lt, re, lit, Holds] using h
    simp [Pow, withDomain₂, powDomain, powTotal, lit, hw]

theorem pow_e : Statement.pow_e := by
  intro a
  cases a <;> simp [Pow, withDomain₂, powDomain, powTotal, E, exp, Complex.exp_ne_zero,
    log_exp_real (show (1 : ℂ).im = 0 by simp)]

theorem exp_zero : Statement.exp_zero := by simp [Statement.exp_zero, exp, lit]

theorem exp_one : Statement.exp_one := by simp [Statement.exp_one, exp, lit, E]

theorem exp_product : Statement.exp_product := by
  intro a b; cases a <;> cases b <;> simp [exp, Mul, Add, Complex.exp_add]

theorem log_one : Statement.log_one := by
  simp [Statement.log_one, log, withDomain, logDomain, lit]

theorem log_e : Statement.log_e := by
  simp [Statement.log_e, log, withDomain, logDomain, lit, E, Complex.exp_ne_zero,
    log_exp_real (show (1 : ℂ).im = 0 by simp)]

theorem log_exp : Statement.log_exp := by
  intro a h
  cases a with
  | none => simp [Eq, re, Holds] at h
  | some w =>
    have hw : w.im = 0 := by
      have : (w.re : ℂ) = w := by simpa [Eq, re, Holds] using h
      rw [← this]; simp
    simp [log, exp, withDomain, logDomain, Complex.exp_ne_zero, log_exp_real hw]

theorem exp_i_pi : Statement.exp_i_pi := by
  intro rest
  cases h : rest.mapM id <;>
    simp [exp, Add, Mul, I, pi, List.mapM_cons, h, Complex.exp_add, mul_comm Complex.I,
      Complex.exp_pi_mul_I, lit]

theorem pow_complex : Statement.pow_complex := by
  intro a b h
  simp only [holds_and, List.mem_cons, List.not_mem_nil, forall_eq_or_imp] at h
  obtain ⟨ha, -, -⟩ := h
  cases a with
  | none => simp [Ne, Holds] at ha
  | some z =>
  have hz : z ≠ 0 := by simpa [Ne, Holds, lit] using ha
  cases b <;> simp [Pow, withDomain₂, powDomain, powTotal, hz, exp, log, withDomain, logDomain, Mul]

theorem exp_half_i_pi : Statement.exp_half_i_pi := by
  intro rest
  have : Pow (lit 2) (lit (-1)) = some 2⁻¹ := by
    rw [lit, Literals.pow_integer _ _ (Or.inl (by norm_num))]; simp
  rw [this]
  have e : Complex.exp (2⁻¹ * (Complex.I * Real.pi)) = Complex.I := by
    rw [show 2⁻¹ * (Complex.I * Real.pi) = Real.pi / 2 * Complex.I by ring, Complex.exp_pi_div_two_mul_I]
  cases h : rest.mapM id <;> simp [exp, Add, Mul, I, pi, List.mapM_cons, h, Complex.exp_add, e]

theorem exp_minus_half_i_pi : Statement.exp_minus_half_i_pi := by
  intro rest
  have : Pow (lit 2) (lit (-1)) = some 2⁻¹ := by
    rw [lit, Literals.pow_integer _ _ (Or.inl (by norm_num))]; simp
  rw [this]
  have e : Complex.exp (-(2⁻¹ * (Complex.I * Real.pi))) = -Complex.I := by
    rw [show -(2⁻¹ * (Complex.I * Real.pi)) = -(Real.pi / 2 * Complex.I) by ring, Complex.exp_neg,
      Complex.exp_pi_div_two_mul_I, Complex.inv_I]
  cases h : rest.mapM id <;> simp [exp, Add, Mul, I, pi, lit, List.mapM_cons, h, Complex.exp_add, e]

theorem log_i : Statement.log_i := by
  simp only [Statement.log_i]
  have : Pow (lit 2) (lit (-1)) = some 2⁻¹ := by
    rw [lit, Literals.pow_integer _ _ (Or.inl (by norm_num))]; simp
  rw [this]
  simp [log, withDomain, logDomain, I, Mul, pi, Complex.log_I]
  ring

end Nary.ArithmeticRules
