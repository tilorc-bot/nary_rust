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

/-- A list of numbers all of which have a value has a list of values. -/
private theorem mapM_some {β : Type*} :
    ∀ xs : List (Option β), (∀ x ∈ xs, x ≠ none) → ∃ l, xs.mapM id = some l
  | [], _ => ⟨[], rfl⟩
  | x :: xs, h => by
    obtain ⟨b, rfl⟩ := Option.ne_none_iff_exists'.mp (h x (by simp))
    obtain ⟨l, hl⟩ := mapM_some xs (fun y hy => h y (by simp [hy]))
    exact ⟨b :: l, by simp [List.mapM_cons, hl]⟩

/-! ### `Add` -/

theorem add_singleton : Statement.add_singleton := by
  intro a; cases a <;> simp [Add]

theorem add_identity : Statement.add_identity := by
  intro xs ys
  simp only [Add, List.mapM_append, List.mapM_cons]
  cases xs.mapM id <;> cases ys.mapM id <;> simp [lit]

theorem add_identity_rule : Statement.add_identity_rule :=
  add_identity.rule add_singleton

theorem add_self : Statement.add_self := by
  intro a; cases a <;> simp [Add, Mul, lit, two_mul]

theorem add_neg_self : Statement.add_neg_self := by
  intro a h
  obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h
  simp [Add, Mul, lit]

/-! ### `Mul` -/

theorem mul_singleton : Statement.mul_singleton := by
  intro a; cases a <;> simp [Mul]

theorem mul_identity : Statement.mul_identity := by
  intro xs ys
  simp only [Mul, List.mapM_append, List.mapM_cons]
  cases xs.mapM id <;> cases ys.mapM id <;> simp [lit]

theorem mul_identity_rule : Statement.mul_identity_rule :=
  mul_identity.rule mul_singleton

theorem mul_absorbing : Statement.mul_absorbing := by
  intro xs ys h
  obtain ⟨l₁, h₁⟩ := mapM_some xs (fun x hx => h x (by simp [hx]))
  obtain ⟨l₂, h₂⟩ := mapM_some ys (fun x hx => h x (by simp [hx]))
  simp [Mul, List.mapM_append, List.mapM_cons, h₁, h₂, lit]

theorem mul_absorbing_rule : Statement.mul_absorbing_rule :=
  mul_absorbing.rule

/-- Without the hypothesis `a ≠ none`, `a * 0 → 0` is wrong: at `a = log(0)`
the left side has no value and the right side is 0. -/
example : Mul [log (lit 0), lit 0] ≠ lit 0 := by
  simp [Mul, log, withDomain, logDomain, lit]

theorem mul_distributive : Statement.mul_distributive := by
  intro a b c
  cases a <;> cases b <;> cases c <;> simp [Mul, Add, mul_add]

theorem mul_inv_self : Statement.mul_inv_self := by
  intro a h _
  obtain ⟨z, rfl, hz⟩ := holds_ne_zero h
  have : z * Complex.exp (-Complex.log z) = 1 := by
    rw [Complex.exp_neg, Complex.exp_log hz, mul_inv_cancel₀ hz]
  simp [Mul, Pow, withDomain₂, powDomain, powTotal, lit, hz, this]

/-! ### `Pow` and `exp` -/

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

/-! ### `Add` and `Mul`: associative and commutative -/

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

theorem add_commutative : Statement.add_commutative := by
  intro xs ys h
  have := congrArg (Option.map Multiset.sum) (values_perm h)
  simpa [values, Add, Option.map_map, Function.comp_def] using this

theorem mul_commutative : Statement.mul_commutative := by
  intro xs ys h
  have := congrArg (Option.map Multiset.prod) (values_perm h)
  simpa [values, Mul, Option.map_map, Function.comp_def] using this

theorem add_associative : Statement.add_associative := by
  intro xs ys zs
  simp only [Add, List.mapM_append, List.mapM_cons]
  cases xs.mapM id <;> cases ys.mapM id <;> cases zs.mapM id <;> simp

theorem mul_associative : Statement.mul_associative := by
  intro xs ys zs
  simp only [Mul, List.mapM_append, List.mapM_cons]
  cases xs.mapM id <;> cases ys.mapM id <;> cases zs.mapM id <;> simp

/-! ### `And` and `Or`

Both are Kleene connectives (`Nary/Logic.lean`): the value of `And l` depends
only on whether some argument is false and whether some argument has no
value, so two lists that agree on both give the same value. -/

private theorem and_of_false {l : List Boolean} (h : ∃ p, some p ∈ l ∧ ¬p) :
    And l = some False := by
  unfold And; simp [h]

private theorem and_of_none {l : List Boolean} (h : ¬∃ p, some p ∈ l ∧ ¬p) (hn : none ∈ l) :
    And l = none := by
  unfold And; simp [h, hn]

private theorem and_of_true {l : List Boolean} (h : ¬∃ p, some p ∈ l ∧ ¬p) (hn : none ∉ l) :
    And l = some True := by
  unfold And; simp [h, hn]

private theorem or_of_true {l : List Boolean} (h : ∃ p, some p ∈ l ∧ p) :
    Or l = some True := by
  unfold Or; simp [h]

private theorem or_of_none {l : List Boolean} (h : ¬∃ p, some p ∈ l ∧ p) (hn : none ∈ l) :
    Or l = none := by
  unfold Or; simp [h, hn]

private theorem or_of_false {l : List Boolean} (h : ¬∃ p, some p ∈ l ∧ p) (hn : none ∉ l) :
    Or l = some False := by
  unfold Or; simp [h, hn]

private theorem and_eq {l₁ l₂ : List Boolean}
    (hf : (∃ p, some p ∈ l₁ ∧ ¬p) ↔ (∃ p, some p ∈ l₂ ∧ ¬p))
    (hn : none ∈ l₁ ↔ none ∈ l₂) : And l₁ = And l₂ := by
  by_cases h₁ : ∃ p, some p ∈ l₁ ∧ ¬p
  · rw [and_of_false h₁, and_of_false (hf.mp h₁)]
  by_cases h₂ : none ∈ l₁
  · rw [and_of_none h₁ h₂, and_of_none (mt hf.mpr h₁) (hn.mp h₂)]
  · rw [and_of_true h₁ h₂, and_of_true (mt hf.mpr h₁) (mt hn.mpr h₂)]

private theorem or_eq {l₁ l₂ : List Boolean}
    (ht : (∃ p, some p ∈ l₁ ∧ p) ↔ (∃ p, some p ∈ l₂ ∧ p))
    (hn : none ∈ l₁ ↔ none ∈ l₂) : Or l₁ = Or l₂ := by
  by_cases h₁ : ∃ p, some p ∈ l₁ ∧ p
  · rw [or_of_true h₁, or_of_true (ht.mp h₁)]
  by_cases h₂ : none ∈ l₁
  · rw [or_of_none h₁ h₂, or_of_none (mt ht.mpr h₁) (hn.mp h₂)]
  · rw [or_of_false h₁ h₂, or_of_false (mt ht.mpr h₁) (mt hn.mpr h₂)]

private theorem and_mem {l₁ l₂ : List Boolean} (h : ∀ x, x ∈ l₁ ↔ x ∈ l₂) :
    And l₁ = And l₂ :=
  and_eq (by simp only [h]) (h none)

private theorem or_mem {l₁ l₂ : List Boolean} (h : ∀ x, x ∈ l₁ ↔ x ∈ l₂) :
    Or l₁ = Or l₂ :=
  or_eq (by simp only [h]) (h none)

theorem and_commutative : Statement.and_commutative :=
  fun _ _ h => and_mem (fun _ => h.mem_iff)

theorem or_commutative : Statement.or_commutative :=
  fun _ _ h => or_mem (fun _ => h.mem_iff)

theorem and_idempotent : Statement.and_idempotent := by
  intro xs ys zs a
  apply and_mem; intro x; simp only [List.mem_append, List.mem_cons]; tauto

theorem or_idempotent : Statement.or_idempotent := by
  intro xs ys zs a
  apply or_mem; intro x; simp only [List.mem_append, List.mem_cons]; tauto

theorem and_singleton : Statement.and_singleton := by
  intro a
  rcases a with _ | p
  · simp [And]
  · by_cases hp : p
    · simp [And, hp]
    · simp [And, hp]; exact ⟨False, not_false⟩

theorem or_singleton : Statement.or_singleton := by
  intro a
  rcases a with _ | p
  · simp [Or]
  · by_cases hp : p
    · simp [Or, hp]; exact ⟨True, trivial⟩
    · simp [Or, hp]

theorem and_identity : Statement.and_identity := by
  intro xs ys
  apply and_eq <;> simp [true, or_and_right, exists_or]

theorem or_identity : Statement.or_identity := by
  intro xs ys
  apply or_eq <;> simp [false, or_and_right, exists_or]

theorem and_absorbing : Statement.and_absorbing := by
  intro xs ys _
  exact and_of_false ⟨False, by simp [Nary.false], not_false⟩

theorem or_absorbing : Statement.or_absorbing := by
  intro xs ys _
  exact or_of_true ⟨True, by simp [Nary.true], trivial⟩

theorem and_associative : Statement.and_associative := by
  intro xs ys zs
  by_cases hf : ∃ p, some p ∈ ys ∧ ¬p
  · have hv := and_of_false hf
    obtain ⟨p, hp, hnp⟩ := hf
    exact (and_of_false ⟨False, by simp [hv], not_false⟩).trans
      (and_of_false ⟨p, by simp [hp], hnp⟩).symm
  by_cases hn : none ∈ ys
  · have hv : And ys = none := and_of_none hf hn
    apply and_eq
    · simp only [List.mem_append, List.mem_cons, hv]
      constructor
      · rintro ⟨p, h | h | h, hp⟩
        · exact ⟨p, by simp [h], hp⟩
        · simp at h
        · exact ⟨p, by simp [h], hp⟩
      · rintro ⟨p, (h | h) | h, hp⟩
        · exact ⟨p, by simp [h], hp⟩
        · exact absurd ⟨p, h, hp⟩ hf
        · exact ⟨p, by simp [h], hp⟩
    · simp [hn, hv]
  · have hv : And ys = some True := and_of_true hf hn
    apply and_eq
    · simp only [List.mem_append, List.mem_cons, hv]
      constructor
      · rintro ⟨p, h | h | h, hp⟩
        · exact ⟨p, by simp [h], hp⟩
        · simp only [Option.some.injEq] at h; exact absurd trivial (h ▸ hp)
        · exact ⟨p, by simp [h], hp⟩
      · rintro ⟨p, (h | h) | h, hp⟩
        · exact ⟨p, by simp [h], hp⟩
        · exact absurd ⟨p, h, hp⟩ hf
        · exact ⟨p, by simp [h], hp⟩
    · simp [hn, hv]

theorem or_associative : Statement.or_associative := by
  intro xs ys zs
  by_cases ht : ∃ p, some p ∈ ys ∧ p
  · have hv := or_of_true ht
    obtain ⟨p, hp, hpp⟩ := ht
    exact (or_of_true ⟨True, by simp [hv], trivial⟩).trans
      (or_of_true ⟨p, by simp [hp], hpp⟩).symm
  by_cases hn : none ∈ ys
  · have hv : Or ys = none := or_of_none ht hn
    apply or_eq
    · simp only [List.mem_append, List.mem_cons, hv]
      constructor
      · rintro ⟨p, h | h | h, hp⟩
        · exact ⟨p, by simp [h], hp⟩
        · simp at h
        · exact ⟨p, by simp [h], hp⟩
      · rintro ⟨p, (h | h) | h, hp⟩
        · exact ⟨p, by simp [h], hp⟩
        · exact absurd ⟨p, h, hp⟩ ht
        · exact ⟨p, by simp [h], hp⟩
    · simp [hn, hv]
  · have hv : Or ys = some False := or_of_false ht hn
    apply or_eq
    · simp only [List.mem_append, List.mem_cons, hv]
      constructor
      · rintro ⟨p, h | h | h, hp⟩
        · exact ⟨p, by simp [h], hp⟩
        · simp only [Option.some.injEq] at h; exact (h ▸ hp : False).elim
        · exact ⟨p, by simp [h], hp⟩
      · rintro ⟨p, (h | h) | h, hp⟩
        · exact ⟨p, by simp [h], hp⟩
        · exact absurd ⟨p, h, hp⟩ ht
        · exact ⟨p, by simp [h], hp⟩
    · simp [hn, hv]

theorem and_identity_rule : Statement.and_identity_rule := and_identity.rule and_singleton
theorem and_idempotent_rule : Statement.and_idempotent_rule := and_idempotent.rule and_singleton
theorem and_absorbing_rule : Statement.and_absorbing_rule := and_absorbing.rule
theorem or_identity_rule : Statement.or_identity_rule := or_identity.rule or_singleton
theorem or_idempotent_rule : Statement.or_idempotent_rule := or_idempotent.rule or_singleton
theorem or_absorbing_rule : Statement.or_absorbing_rule := or_absorbing.rule

/-! ### All of them -/

/-- Every generated statement is proved. -/
theorem proved : Proved := by
  exact {
    add_associative := add_associative
    add_commutative := add_commutative
    add_singleton := add_singleton
    add_identity := add_identity
    add_self := add_self
    add_neg_self := add_neg_self
    add_identity_rule := add_identity_rule
    mul_associative := mul_associative
    mul_commutative := mul_commutative
    mul_singleton := mul_singleton
    mul_identity := mul_identity
    mul_absorbing := mul_absorbing
    mul_distributive := mul_distributive
    mul_inv_self := mul_inv_self
    mul_identity_rule := mul_identity_rule
    mul_absorbing_rule := mul_absorbing_rule
    pow_one := pow_one
    pow_zero := pow_zero
    exp_log := exp_log
    and_associative := and_associative
    and_commutative := and_commutative
    and_singleton := and_singleton
    and_idempotent := and_idempotent
    and_identity := and_identity
    and_absorbing := and_absorbing
    and_idempotent_rule := and_idempotent_rule
    and_identity_rule := and_identity_rule
    and_absorbing_rule := and_absorbing_rule
    or_associative := or_associative
    or_commutative := or_commutative
    or_singleton := or_singleton
    or_idempotent := or_idempotent
    or_identity := or_identity
    or_absorbing := or_absorbing
    or_idempotent_rule := or_idempotent_rule
    or_identity_rule := or_identity_rule
    or_absorbing_rule := or_absorbing_rule
  }

end Nary.ArithmeticRules
