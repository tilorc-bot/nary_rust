/-
Proofs of the rules and facts of `python/nary/arithmetic_rules.py`, written
by hand.

The statements are generated from Python into
`Nary/ArithmeticRules/Statements.lean` as `Statement.add_zero` and so on.
Each theorem here proves one of them under the same name, and `proved` at the
end collects them all into the generated structure `Proved`. So `lake build`
fails if a statement has no proof here, or if a proof no longer fits its
statement after the rule changed in Python.

Each theorem is `Nary.ArithmeticRules.add_zero` and so on, not `Nary.add_zero`,
so that it cannot be confused with Mathlib's `add_zero`.
-/
import Nary.ArithmeticRules.Statements

namespace Nary.ArithmeticRules

/-! ### The rules -/

/-- The condition `Ne(a, 0)` holds exactly when `a` has a value that is not 0. -/
private theorem holds_ne_zero {a : Number} (h : Holds (Ne a (lit 0))) :
    ∃ z, a = some z ∧ z ≠ 0 := by
  cases a with
  | none => simp [Ne, Holds] at h
  | some z => exact ⟨z, rfl, by simpa [Ne, Holds, lit] using h⟩

theorem add_zero : Statement.add_zero := by
  intro a; cases a <;> simp [Add, lit]

theorem mul_one : Statement.mul_one := by
  intro a; cases a <;> simp [Mul, lit]

theorem mul_zero : Statement.mul_zero := by
  intro a h
  obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [Mul, lit]

/-- Without the hypothesis `a ≠ none`, `a * 0 → 0` is wrong: at `a = log(0)`
the left side has no value and the right side is 0. -/
example : Mul [log (lit 0), lit 0] ≠ lit 0 := by
  simp [Mul, log, withDomain, logDomain, lit]

theorem add_self : Statement.add_self := by
  intro a; cases a <;> simp [Add, Mul, lit, two_mul]

theorem sub_self : Statement.sub_self := by
  intro a h
  obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [Add, Mul, lit]

theorem div_self : Statement.div_self := by
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

/-! ### The facts about `Add` and `Mul` -/

/-- The values of the arguments as a multiset (which forgets their order),
or `none` if one argument has no value. -/
private abbrev values (xs : List Number) : Option (Multiset ℂ) :=
  (xs.mapM id).map (fun l : List ℂ => (l : Multiset ℂ))

private theorem values_cons (x : Number) (l : List Number) :
    values (x :: l) = x.bind (fun a => (values l).map (Multiset.cons a)) := by
  cases x <;> cases h : l.mapM id <;> simp [values, List.mapM_cons, h]

/-- Reordering the arguments does not change `values`. -/
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

/-! ### All of them -/

/-- Every generated statement is proved. -/
theorem proved : Proved where
  add_zero := add_zero
  mul_one := mul_one
  mul_zero := mul_zero
  add_self := add_self
  sub_self := sub_self
  div_self := div_self
  pow_one := pow_one
  pow_zero := pow_zero
  exp_log := exp_log
  add_unordered := add_unordered
  add_flat := add_flat
  mul_unordered := mul_unordered
  mul_flat := mul_flat

end Nary.ArithmeticRules
