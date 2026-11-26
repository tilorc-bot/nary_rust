import Nary.Literals
import Nary.ArithmeticRules.Statements
import Nary.Autosimp.Statements
import Nary.LogPower.Statements

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

theorem one_pow : Autosimp.Statement.one_pow := by
  intro a h
  obtain ⟨w, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [Pow, withDomain₂, powDomain, powTotal, lit]

theorem zero_pow : Autosimp.Statement.zero_pow := by
  intro a h _
  cases a with
  | none => simp [Gt, Lt, re, Holds] at h
  | some w =>
    have hw : 0 < w.re := by simpa [Gt, Lt, re, lit, Holds] using h
    simp [Pow, withDomain₂, powDomain, powTotal, lit, hw]

theorem e_pow : Autosimp.Statement.e_pow := by
  intro a
  cases a <;> simp [Pow, withDomain₂, powDomain, powTotal, E, exp, Complex.exp_ne_zero,
    log_exp_real (show (1 : ℂ).im = 0 by simp)]

theorem exp_zero : Autosimp.Statement.exp_zero := by simp [Autosimp.Statement.exp_zero, exp, lit]

theorem exp_one : Autosimp.Statement.exp_one := by simp [Autosimp.Statement.exp_one, exp, lit, E]

theorem log_one : Autosimp.Statement.log_one := by
  simp [Autosimp.Statement.log_one, log, withDomain, logDomain, lit]

theorem log_e : Autosimp.Statement.log_e := by
  simp [Autosimp.Statement.log_e, log, withDomain, logDomain, lit, E, Complex.exp_ne_zero,
    log_exp_real (show (1 : ℂ).im = 0 by simp)]

theorem log_exp : Autosimp.Statement.log_exp := by
  intro a h
  cases a with
  | none => simp [Eq, re, Holds] at h
  | some w =>
    have hw : w.im = 0 := by
      have : (w.re : ℂ) = w := by simpa [Eq, re, Holds] using h
      rw [← this]; simp
    simp [log, exp, withDomain, logDomain, Complex.exp_ne_zero, log_exp_real hw]

theorem holds_pos {a : Number} (h : Holds (Gt a (lit 0))) : ∃ r : ℝ, 0 < r ∧ a = some (r : ℂ) := by
  cases a with
  | none => simp [Gt, Lt, Holds] at h
  | some z =>
    by_cases hi : z.im = 0
    · refine ⟨z.re, by simpa [Gt, Lt, lit, Holds, hi] using h, ?_⟩
      congr 1; exact Complex.ext (by simp) (by simp [hi])
    · simp [Gt, Lt, lit, Holds, hi] at h

private theorem holds_neg {a : Number} (h : Holds (Lt a (lit 0))) : ∃ r : ℝ, r < 0 ∧ a = some (r : ℂ) := by
  cases a with
  | none => simp [Lt, Holds] at h
  | some z =>
    by_cases hi : z.im = 0
    · refine ⟨z.re, by simpa [Lt, lit, Holds, hi] using h, ?_⟩
      congr 1; exact Complex.ext (by simp) (by simp [hi])
    · simp [Lt, lit, Holds, hi] at h

private theorem holds_real {b : Number} (h : Holds (Eq (re b) b)) : ∃ r : ℝ, b = some (r : ℂ) := by
  cases b with
  | none => simp [Eq, re, Holds] at h
  | some w => exact ⟨w.re, by simpa [Eq, re, Holds, eq_comm] using h⟩

theorem log_real_pos {r : ℝ} (hr : 0 < r) : Complex.log (r : ℂ) = (Real.log r : ℂ) :=
  (Complex.ofReal_log hr.le).symm

private theorem log_neg_real {r : ℝ} (hr : 0 < r) : Complex.log (-(r : ℂ)) = Real.log r + Real.pi * Complex.I := by
  rw [show -(r : ℂ) = r * (-1) by ring, Complex.log_ofReal_mul hr (by norm_num), Complex.log_neg_one]

private theorem log_exp_mul (s t : ℝ) : Complex.log (Complex.exp (s * t)) = s * t := by
  rw [← Complex.ofReal_mul, ← Complex.ofReal_exp, ← Complex.ofReal_log (Real.exp_pos _).le, Real.log_exp]

private theorem pow_real {r : ℝ} (hr : 0 < r) (s : ℝ) :
    Pow (some (r : ℂ)) (some (s : ℂ)) = some ((Real.exp (s * Real.log r) : ℝ) : ℂ) := by
  have h1 : (r : ℂ) ≠ 0 := by exact_mod_cast hr.ne'
  simp [Pow, withDomain₂, powDomain, powTotal, h1, log_real_pos hr]

theorem log_pow : LogPower.Statement.log_pow := by
  intro a b h
  simp only [holds_and, List.mem_cons, List.not_mem_nil, forall_eq_or_imp] at h
  obtain ⟨ha, hb, -⟩ := h
  obtain ⟨r, hr, rfl⟩ := holds_pos ha
  obtain ⟨s, rfl⟩ := holds_real hb
  have h1 : (r : ℂ) ≠ 0 := by exact_mod_cast hr.ne'
  have h2 : ((Real.exp (s * Real.log r) : ℝ) : ℂ) ≠ 0 := by exact_mod_cast (Real.exp_pos _).ne'
  rw [pow_real hr]
  simp [log, withDomain, logDomain, Mul, h1, log_exp_mul, log_real_pos hr]

theorem pow_mul_pos {r : ℝ} (hr : 0 < r) (x a : Number) :
    Pow (Mul [some (r : ℂ), x]) a = Mul [Pow (some (r : ℂ)) a, Pow x a] := by
  have h1 : (r : ℂ) ≠ 0 := by exact_mod_cast hr.ne'
  cases x with
  | none => cases a <;> simp [Pow, withDomain₂, Mul]
  | some u =>
  cases a with
  | none => simp [Pow, withDomain₂, Mul]
  | some w =>
  by_cases hu : u = 0
  · subst hu; by_cases hw : 0 < w.re <;> simp [Pow, withDomain₂, powDomain, powTotal, Mul, h1, hw]
  · simp [Pow, withDomain₂, powDomain, powTotal, Mul, h1, hu, Complex.log_ofReal_mul hr hu,
      log_real_pos hr, mul_add, Complex.exp_add]

end Nary.ArithmeticRules
