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

theorem mul_repeats : Statement.mul_repeats := by
  intro a
  cases a with
  | none => simp [Mul, Pow, withDomain₂]
  | some z =>
    by_cases hz : z = 0
    · simp [Mul, Pow, withDomain₂, powDomain, powTotal, lit, hz]
    · simp [Mul, Pow, withDomain₂, powDomain, powTotal, lit, hz, two_mul, Complex.exp_add,
        Complex.exp_log hz]

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

theorem add_identity_law : Statement.add_identity_law := by
  refine ⟨by simp [Add, lit], fun a => by cases a <;> simp [Add], fun xs ys => ?_⟩
  simp only [Add, List.mapM_append, List.mapM_cons]
  cases xs.mapM id <;> cases ys.mapM id <;> simp [lit]

theorem mul_identity_law : Statement.mul_identity_law := by
  refine ⟨by simp [Mul, lit], fun a => by cases a <;> simp [Mul], fun xs ys => ?_⟩
  simp only [Mul, List.mapM_append, List.mapM_cons]
  cases xs.mapM id <;> cases ys.mapM id <;> simp [lit]

private theorem mapM_some {l : List Number} (h : ∀ x ∈ l, x ≠ none) : ∃ v, l.mapM id = some v := by
  induction l with
  | nil => exact ⟨[], rfl⟩
  | cons x l ih =>
    obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp (h x (by simp))
    obtain ⟨v, hv⟩ := ih (fun y hy => h y (by simp [hy]))
    exact ⟨z :: v, by simp [List.mapM_cons, hv]⟩

theorem mul_absorbing_law : Statement.mul_absorbing_law := by
  intro xs ys h
  obtain ⟨v, hv⟩ := mapM_some (fun x hx => h x (List.mem_append_left _ hx))
  obtain ⟨w, hw⟩ := mapM_some (fun x hx => h x (List.mem_append_right _ hx))
  simp [Mul, List.mapM_append, List.mapM_cons, hv, hw, lit]

theorem add_repeats_law : Statement.add_repeats_law := by
  refine ⟨fun a => by cases a <;> simp [Mul, lit], fun a h => ?_, fun a m n _ => ?_⟩
  · cases a <;> simp_all [Mul, Add, lit]
  · cases a <;> cases m <;> cases n <;> simp [Mul, Add, add_mul]

theorem mul_repeats_law : Statement.mul_repeats_law := by
  refine ⟨fun a => ?_, fun a h => ?_, fun a m n h => ?_⟩
  · cases a with
    | none => simp [Pow, withDomain₂]
    | some z =>
      by_cases hz : z = 0
      · simp [Pow, withDomain₂, powDomain, powTotal, lit, hz]
      · simp [Pow, withDomain₂, powDomain, powTotal, lit, hz, Complex.exp_log hz]
  · cases a with
    | none => simp [Pow, withDomain₂] at h
    | some z =>
      by_cases hz : z = 0
      · simp [Pow, withDomain₂, powDomain, hz, lit] at h
      · simp [Pow, withDomain₂, powDomain, powTotal, hz, lit, Mul]
  · cases a with
    | none => simp [Pow, withDomain₂, Mul, Add]
    | some z =>
      cases m with
      | none => simp [Pow, withDomain₂, Mul, Add]
      | some p =>
        cases n with
        | none => simp [Pow, withDomain₂, Mul, Add]
        | some q =>
          by_cases hz : z = 0
          · subst hz
            by_cases hp : 0 < p.re <;> by_cases hq : 0 < q.re <;>
              simp [Pow, withDomain₂, powDomain, powTotal, Mul, Add, hp, hq] at h ⊢ <;> linarith
          · simp [Pow, withDomain₂, powDomain, powTotal, hz, Mul, Add, add_mul, Complex.exp_add]

private theorem and_congr_values {xs ys : List Boolean}
    (h : ∀ p : Prop, ¬p → (some p ∈ xs ↔ some p ∈ ys)) (hn : none ∈ xs ↔ none ∈ ys) :
    And xs = And ys := by
  have h1 : (∃ p, some p ∈ xs ∧ ¬p) = (∃ p, some p ∈ ys ∧ ¬p) :=
    propext ⟨fun ⟨p, m, hp⟩ => ⟨p, (h p hp).1 m, hp⟩, fun ⟨p, m, hp⟩ => ⟨p, (h p hp).2 m, hp⟩⟩
  unfold And
  split_ifs <;> simp_all

private theorem or_congr_values {xs ys : List Boolean}
    (h : ∀ p : Prop, p → (some p ∈ xs ↔ some p ∈ ys)) (hn : none ∈ xs ↔ none ∈ ys) :
    Or xs = Or ys := by
  have h1 : (∃ p, some p ∈ xs ∧ p) = (∃ p, some p ∈ ys ∧ p) :=
    propext ⟨fun ⟨p, m, hp⟩ => ⟨p, (h p hp).1 m, hp⟩, fun ⟨p, m, hp⟩ => ⟨p, (h p hp).2 m, hp⟩⟩
  unfold Or
  split_ifs <;> simp_all

theorem and_unordered : Statement.and_unordered := fun _ _ h =>
  and_congr_values (fun _ _ => h.mem_iff) h.mem_iff

theorem or_unordered : Statement.or_unordered := fun _ _ h =>
  or_congr_values (fun _ _ => h.mem_iff) h.mem_iff

private theorem and_of_false {xs : List Boolean} (h : ∃ p, some p ∈ xs ∧ ¬p) :
    And xs = some False := by
  rw [And, ite_eq_left_of_eq_true _ _ (eq_true h)]

private theorem or_of_true {xs : List Boolean} (h : ∃ p, some p ∈ xs ∧ p) :
    Or xs = some True := by
  rw [Or, ite_eq_left_of_eq_true _ _ (eq_true h)]

theorem and_flat : Statement.and_flat := by
  intro xs ys zs
  by_cases h1 : ∃ p, some p ∈ ys ∧ ¬p
  · obtain ⟨p, m, hp⟩ := h1
    rw [and_of_false ⟨p, m, hp⟩, and_of_false ⟨False, by simp, id⟩,
      and_of_false ⟨p, by simp [m], hp⟩]
  · simp only [not_exists, not_and, not_not] at h1
    by_cases h2 : none ∈ ys
    · have : And ys = none := by simp [And, h2]; exact h1
      rw [this]
      exact and_congr_values (fun q hq => by
        have hy : some q ∉ ys := fun h => hq (h1 q h)
        simp [hy]) (by simp [h2])
    · have : And ys = some True := by simp [And, h2]; exact h1
      rw [this]
      exact and_congr_values (fun q hq => by
        have hy : some q ∉ ys := fun h => hq (h1 q h)
        simp [hy]
        tauto) (by simp [h2])

theorem or_flat : Statement.or_flat := by
  intro xs ys zs
  by_cases h1 : ∃ p, some p ∈ ys ∧ p
  · obtain ⟨p, m, hp⟩ := h1
    rw [or_of_true ⟨p, m, hp⟩, or_of_true ⟨True, by simp, trivial⟩, or_of_true ⟨p, by simp [m], hp⟩]
  · simp only [not_exists, not_and] at h1
    by_cases h2 : none ∈ ys
    · have : Or ys = none := by simp [Or, h2]; exact h1
      rw [this]
      exact or_congr_values (fun q hq => by
        have hy : some q ∉ ys := fun h => h1 q h hq
        simp [hy]) (by simp [h2])
    · have : Or ys = some False := by simp [Or, h2]; exact h1
      rw [this]
      exact or_congr_values (fun q hq => by
        have hy : some q ∉ ys := fun h => h1 q h hq
        simp [hy]
        tauto) (by simp [h2])

theorem and_identity_law : Statement.and_identity_law := by
  refine ⟨by simp [And, true], fun a => ?_, fun xs ys => ?_⟩
  · cases a with
    | none => simp [And]
    | some p =>
      by_cases hp : p
      · simp [And, hp]
      · simp [And, hp]
        exact ⟨False, id⟩
  · exact and_congr_values (fun p hp => by simp [true, hp]) (by simp [true])

theorem or_identity_law : Statement.or_identity_law := by
  refine ⟨by simp [Or, false], fun a => ?_, fun xs ys => ?_⟩
  · cases a with
    | none => simp [Or]
    | some p =>
      by_cases hp : p
      · simp [Or, hp]
        exact ⟨True, trivial⟩
      · simp [Or, hp]
  · exact or_congr_values (fun p hp => by simp [false, hp]) (by simp [false])

theorem and_absorbing_law : Statement.and_absorbing_law := by
  intro xs ys _
  rw [And, ite_eq_left_of_eq_true _ _ (eq_true ⟨False, by simp [false], id⟩)]
  rfl

theorem or_absorbing_law : Statement.or_absorbing_law := by
  intro xs ys _
  rw [Or, ite_eq_left_of_eq_true _ _ (eq_true ⟨True, by simp [true], trivial⟩)]
  rfl

theorem and_idempotent_law : Statement.and_idempotent_law := by
  intro xs ys zs a
  exact and_congr_values (fun p _ => by simp; tauto) (by simp; tauto)

theorem or_idempotent_law : Statement.or_idempotent_law := by
  intro xs ys zs a
  exact or_congr_values (fun p _ => by simp; tauto) (by simp; tauto)

theorem not_involution_law : Statement.not_involution_law := by
  intro a
  cases a <;> simp [Not]

theorem proved : Proved where
  add_identity := add_identity
  add_self := add_self
  add_inverse := add_inverse
  mul_identity := mul_identity
  mul_absorbing := mul_absorbing
  mul_repeats := mul_repeats
  mul_inverse := mul_inverse
  pow_one := pow_one
  pow_zero := pow_zero
  exp_log := exp_log
  add_flat := add_flat
  add_unordered := add_unordered
  add_identity_law := add_identity_law
  add_repeats_law := add_repeats_law
  mul_flat := mul_flat
  mul_unordered := mul_unordered
  mul_identity_law := mul_identity_law
  mul_absorbing_law := mul_absorbing_law
  mul_repeats_law := mul_repeats_law
  and_flat := and_flat
  and_unordered := and_unordered
  and_identity_law := and_identity_law
  and_absorbing_law := and_absorbing_law
  and_idempotent_law := and_idempotent_law
  or_flat := or_flat
  or_unordered := or_unordered
  or_identity_law := or_identity_law
  or_absorbing_law := or_absorbing_law
  or_idempotent_law := or_idempotent_law
  not_involution_law := not_involution_law

end Nary.ArithmeticRules
