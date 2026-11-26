import Nary.ArithmeticRules
import Nary.Normal.Statements

namespace Nary.Normal

private theorem holds_gt_re_zero (a : Number) : Holds (Gt (re a) (lit 0)) ↔ ∃ u, a = some u ∧ 0 < u.re := by
  cases a <;> simp [Gt, Lt, re, lit, Holds]

theorem collect_terms : Statement.collect_terms := by
  intro a x b; cases a <;> cases x <;> cases b <;> simp [Add, Mul, add_mul]

theorem add_zero : Statement.add_zero := by
  intro a; cases a <;> simp [Add, lit]

theorem mul_one : Statement.mul_one := by
  intro a; cases a <;> simp [Mul, lit]

theorem mul_zero : Statement.mul_zero := by
  intro a h
  obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [Mul, lit]

theorem distribute : Statement.distribute := by
  intro a x y; cases a <;> cases x <;> cases y <;> simp [Add, Mul, mul_add]

theorem collect_powers : Statement.collect_powers := by
  intro x a b h
  cases x with
  | none => simp [Ne, Holds] at h
  | some z =>
    have hz : z ≠ 0 := by simpa [Ne, Holds, lit] using h
    cases a <;> cases b <;>
      simp [Pow, Mul, Add, withDomain₂, powDomain, powTotal, hz, add_mul, Complex.exp_add]

theorem collect_positive_powers : Statement.collect_positive_powers := by
  intro x a b h
  simp only [holds_and, List.mem_cons, List.not_mem_nil, forall_eq_or_imp, holds_gt_re_zero] at h
  obtain ⟨⟨u, rfl, hu⟩, ⟨w, rfl, hw⟩, -⟩ := h
  cases x with
  | none => simp [Pow, Mul, withDomain₂]
  | some z =>
    by_cases hz : z = 0
    · simp [Pow, Mul, Add, withDomain₂, powDomain, powTotal, hz, hu, hw, add_pos hu hw]
    · simp [Pow, Mul, Add, withDomain₂, powDomain, powTotal, hz, add_mul, Complex.exp_add]

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
  cases a with
  | none => simp [Ne, Holds] at h
  | some z =>
    have hz : z ≠ 0 := by simpa [Ne, Holds, lit] using h
    simp [Pow, withDomain₂, powDomain, powTotal, lit, hz]

theorem exp_pow_integer : Statement.exp_pow_integer := by
  intro a n h
  obtain ⟨k, rfl⟩ := Literals.integer_of_holds h
  cases a with
  | none => simp [exp, Pow, withDomain₂, Mul]
  | some w =>
    rw [exp, Option.map_some, Literals.pow_integer _ _ (Or.inl (Complex.exp_ne_zero w))]
    simp [exp, Mul, lit, Complex.exp_int_mul]

theorem mul_pow_integer : Statement.mul_pow_integer := by
  intro x y n h
  obtain ⟨k, rfl⟩ := Literals.integer_of_holds h
  cases x with
  | none => simp [Pow, withDomain₂, Mul]
  | some u =>
  cases y with
  | none => simp [Pow, withDomain₂, Mul]
  | some v =>
  by_cases hk : 0 < k
  · simp only [Mul, List.mapM_cons, List.mapM_nil]
    simp [Literals.pow_integer _ _ (Or.inr hk), mul_zpow]
  · by_cases hu : u = 0
    · subst hu; simp [Mul, Literals.pow_zero_nonpositive k (not_lt.mp hk)]
    by_cases hv : v = 0
    · subst hv; simp [Mul, Literals.pow_zero_nonpositive k (not_lt.mp hk)]
    simp [Mul, Literals.pow_integer _ _ (Or.inl hu), Literals.pow_integer _ _ (Or.inl hv),
      Literals.pow_integer _ _ (Or.inl (mul_ne_zero hu hv)), mul_zpow]

theorem pow_pow_integer : Statement.pow_pow_integer := by
  intro x a n h
  simp only [holds_and, List.mem_cons, List.not_mem_nil, forall_eq_or_imp] at h
  obtain ⟨hn, hx, -⟩ := h
  obtain ⟨k, rfl⟩ := Literals.integer_of_holds hn
  cases x with
  | none => simp [Ne, Holds] at hx
  | some z =>
  have hz : z ≠ 0 := by simpa [Ne, Holds, lit] using hx
  cases a with
  | none => simp [Pow, withDomain₂, Mul]
  | some w =>
  have hp : Pow (some z) (some w) = some (Complex.exp (w * Complex.log z)) := by
    simp [Pow, withDomain₂, powDomain, powTotal, hz]
  rw [hp, Literals.pow_integer _ _ (Or.inl (Complex.exp_ne_zero _))]
  simp [Pow, withDomain₂, powDomain, powTotal, hz, Mul, lit, ← Complex.exp_int_mul]
  ring_nf

theorem pow_pow_positive_integer : Statement.pow_pow_positive_integer := by
  intro x a n h
  simp only [holds_and, List.mem_cons, List.not_mem_nil, forall_eq_or_imp] at h
  obtain ⟨hn, hpos, -⟩ := h
  obtain ⟨k, rfl⟩ := Literals.integer_of_holds hn
  have hk : 0 < k := by simpa [Gt, Lt, lit, Holds] using hpos
  cases a with
  | none => simp [Pow, withDomain₂, Mul]
  | some w =>
  cases x with
  | none => simp [Pow, withDomain₂]
  | some z =>
  by_cases hz : z = 0
  · subst hz
    by_cases hw : 0 < w.re
    · have hp : Pow (some 0) (some w) = some 0 := by simp [Pow, withDomain₂, powDomain, powTotal, hw]
      rw [hp, Literals.pow_integer _ _ (Or.inr hk)]
      simp [Pow, withDomain₂, powDomain, powTotal, Mul, lit, hw, hk, zero_zpow k hk.ne']
    · have hp : Pow (some 0) (some w) = none := by simp [Pow, withDomain₂, powDomain, hw]
      rw [hp]
      have : ¬ 0 < w.re * k := fun h => hw (pos_of_mul_pos_left h (by exact_mod_cast hk.le))
      simp [Pow, withDomain₂, powDomain, Mul, lit, this]
  · have hp : Pow (some z) (some w) = some (Complex.exp (w * Complex.log z)) := by
      simp [Pow, withDomain₂, powDomain, powTotal, hz]
    rw [hp, Literals.pow_integer _ _ (Or.inl (Complex.exp_ne_zero _))]
    simp [Pow, withDomain₂, powDomain, powTotal, hz, Mul, lit, ← Complex.exp_int_mul]
    ring_nf

theorem split_exponent : Statement.split_exponent := by
  intro b n x h
  cases b with
  | none => simp [Ne, Holds] at h
  | some z =>
    have hz : z ≠ 0 := by simpa [Ne, Holds, lit] using h
    cases n <;> cases x <;>
      simp [Pow, Mul, Add, withDomain₂, powDomain, powTotal, hz, add_mul, Complex.exp_add]

theorem zero_base : Statement.zero_base := by
  intro c x h _
  cases c with
  | none => simp [Gt, Lt, Holds] at h
  | some u =>
    have hu : u.im = 0 ∧ 0 < u.re := by
      by_cases hi : u.im = 0
      · exact ⟨hi, by simpa [Gt, Lt, lit, Holds, hi] using h⟩
      · simp [Gt, Lt, lit, Holds, hi] at h
    cases x with
    | none => simp [Pow, withDomain₂, Mul]
    | some w =>
      simp [Pow, withDomain₂, powDomain, powTotal, Mul, lit, hu.1, mul_pos_iff_of_pos_left hu.2]

theorem pow_positive_factor : Statement.pow_positive_factor := by
  intro c x a h
  obtain ⟨r, hr, rfl⟩ := ArithmeticRules.holds_pos h
  exact ArithmeticRules.pow_mul_pos hr x a

theorem combine_radicals : Statement.combine_radicals := by
  intro a c b h
  simp only [holds_and, List.mem_cons, List.not_mem_nil, forall_eq_or_imp] at h
  obtain ⟨ha, hb, -⟩ := h
  obtain ⟨r, hr, rfl⟩ := ArithmeticRules.holds_pos ha
  obtain ⟨q, -, rfl⟩ := ArithmeticRules.holds_pos hb
  exact (ArithmeticRules.pow_mul_pos hr _ c).symm

theorem collect_parallel_powers : Statement.collect_parallel_powers := by
  intro x a c h
  obtain ⟨r, hr, rfl⟩ := ArithmeticRules.holds_pos h
  cases x with
  | none => cases a <;> simp [Pow, withDomain₂, Mul, Add]
  | some z =>
  cases a with
  | none => simp [Pow, withDomain₂, Mul, Add]
  | some w =>
  by_cases hz : z = 0
  · subst hz
    have h1 : 0 < r * w.re ↔ 0 < w.re := mul_pos_iff_of_pos_left hr
    have h2 : 0 < (1 + r) * w.re ↔ 0 < w.re := mul_pos_iff_of_pos_left (by linarith)
    by_cases hw : 0 < w.re <;> simp [Pow, withDomain₂, powDomain, powTotal, Mul, Add, lit, h1, h2, hw]
  · simp [Pow, withDomain₂, powDomain, powTotal, Mul, Add, lit, hz, ← Complex.exp_add]
    ring_nf

end Nary.Normal
