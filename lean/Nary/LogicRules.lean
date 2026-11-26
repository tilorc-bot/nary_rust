import Nary.LogicRules.Statements

namespace Nary.LogicRules

macro "boolean" : tactic => `(tactic| (split_ifs <;> simp_all [-eq_iff_iff]))

theorem and_identity : Statement.and_identity := by
  intro a; rcases a with _ | q <;> simp only [And, true] <;> boolean

theorem and_absorbing : Statement.and_absorbing := by
  intro a h; simp only [And, false]; boolean

theorem and_idempotent : Statement.and_idempotent := by
  intro a; rcases a with _ | q <;> simp only [And] <;> boolean

theorem and_empty : Statement.and_empty := by
  simp only [Statement.and_empty, And, Nary.true]; boolean

theorem and_single : Statement.and_single := by
  intro a; rcases a with _ | q <;> simp only [And] <;> boolean

theorem and_contradiction : Statement.and_contradiction := by
  intro a h; rcases a with _ | q <;> simp only [And, Not, false, Option.map] <;> boolean

theorem or_identity : Statement.or_identity := by
  intro a; rcases a with _ | q <;> simp only [Or, false] <;> boolean

theorem or_absorbing : Statement.or_absorbing := by
  intro a h; simp only [Or, true]; boolean

theorem or_idempotent : Statement.or_idempotent := by
  intro a; rcases a with _ | q <;> simp only [Or] <;> boolean

theorem or_empty : Statement.or_empty := by
  simp only [Statement.or_empty, Or, Nary.false]; boolean

theorem or_single : Statement.or_single := by
  intro a; rcases a with _ | q <;> simp only [Or] <;> boolean

theorem or_excluded_middle : Statement.or_excluded_middle := by
  intro a h; rcases a with _ | q <;> simp only [Or, Not, true, Option.map] <;> boolean

theorem not_not : Statement.not_not := by
  intro a; cases a <;> simp [Not]

theorem not_true : Statement.not_true := by
  simp [Statement.not_true, Not, Nary.true, Nary.false]

theorem not_false : Statement.not_false := by
  simp [Statement.not_false, Not, Nary.true, Nary.false]

theorem not_eq : Statement.not_eq := by
  intro a b; cases a <;> cases b <;> simp [Not, Eq, Ne]

theorem not_ne : Statement.not_ne := by
  intro a b; cases a <;> cases b <;> simp [Not, Eq, Ne]

theorem not_lt : Statement.not_lt := by
  intro a b; cases a <;> cases b <;> simp [Not, Lt, Le, Ge]
  split_ifs <;> simp_all [and_comm]

theorem not_le : Statement.not_le := by
  intro a b; cases a <;> cases b <;> simp [Not, Lt, Le, Gt]
  split_ifs <;> simp_all [and_comm]

theorem not_gt : Statement.not_gt := by
  intro a b; cases a <;> cases b <;> simp [Not, Lt, Le, Gt]
  split_ifs <;> simp_all [and_comm]

theorem not_ge : Statement.not_ge := by
  intro a b; cases a <;> cases b <;> simp [Not, Lt, Le, Ge]
  split_ifs <;> simp_all [and_comm]

theorem eq_self : Statement.eq_self := by
  intro a h; obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h; simp [Eq, true]

theorem ne_self : Statement.ne_self := by
  intro a h; obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp h; simp [Ne, false]

private theorem real_of_holds {z : ℂ} (h : Holds (Eq (re (some z)) (some z))) : z.im = 0 := by
  have : (z.re : ℂ) = z := by simpa [Eq, re, Holds] using h
  rw [← this]; simp

theorem lt_self : Statement.lt_self := by
  intro a h ha; obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp ha
  simp [Lt, false, real_of_holds h]

theorem le_self : Statement.le_self := by
  intro a h ha; obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp ha
  simp [Le, true, real_of_holds h]

theorem gt_self : Statement.gt_self := by
  intro a h ha; obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp ha
  simp [Gt, Lt, false, real_of_holds h]

theorem ge_self : Statement.ge_self := by
  intro a h ha; obtain ⟨z, rfl⟩ := Option.ne_none_iff_exists'.mp ha
  simp [Ge, Le, true, real_of_holds h]

theorem and_unordered : Statement.and_unordered := by
  intro xs ys h
  have e : ∀ a, a ∈ xs ↔ a ∈ ys := fun _ => h.mem_iff
  unfold And; split_ifs <;> simp_all

theorem or_unordered : Statement.or_unordered := by
  intro xs ys h
  have e : ∀ a, a ∈ xs ↔ a ∈ ys := fun _ => h.mem_iff
  unfold Or; split_ifs <;> simp_all

theorem not_and : Statement.not_and := by
  intro p ps
  by_cases hA : ∃ q, some q ∈ ps ∧ ¬q <;> by_cases hN : none ∈ ps <;>
    rcases p with _ | q <;> (try by_cases hq : q) <;> simp [And, Or, Not, -eq_iff_iff, *]

theorem not_or : Statement.not_or := by
  intro p ps
  by_cases hA : ∃ q, some q ∈ ps ∧ q <;> by_cases hN : none ∈ ps <;>
    rcases p with _ | q <;> (try by_cases hq : q) <;> simp [And, Or, Not, -eq_iff_iff, *]

theorem and_absorption : Statement.and_absorption := by
  intro p ps h
  by_cases hA : ∃ q, some q ∈ ps ∧ q <;>
    rcases p with _ | q <;> (try by_cases hq : q) <;> simp [And, Or, -eq_iff_iff, *]

theorem or_absorption : Statement.or_absorption := by
  intro p ps h
  by_cases hA : ∃ q, some q ∈ ps ∧ ¬q <;>
    rcases p with _ | q <;> (try by_cases hq : q) <;> simp [And, Or, -eq_iff_iff, *]

end Nary.LogicRules
