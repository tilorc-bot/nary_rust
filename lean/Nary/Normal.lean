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

end Nary.Normal
