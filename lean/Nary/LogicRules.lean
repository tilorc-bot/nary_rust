import Nary.Autosimp.Statements
import Nary.LogicRules.Statements

namespace Nary.LogicRules

macro "boolean" : tactic => `(tactic| (split_ifs <;> simp_all [-eq_iff_iff]))

theorem not_not : Autosimp.Statement.not_not := by
  intro a; cases a <;> simp [Not]

theorem not_true : Autosimp.Statement.not_true := by
  simp [Autosimp.Statement.not_true, Not, Nary.true, Nary.false]

theorem not_false : Autosimp.Statement.not_false := by
  simp [Autosimp.Statement.not_false, Not, Nary.true, Nary.false]

theorem not_eq : Autosimp.Statement.not_eq := by
  intro a b; cases a <;> cases b <;> simp [Not, Eq, Ne]

theorem not_ne : Autosimp.Statement.not_ne := by
  intro a b; cases a <;> cases b <;> simp [Not, Eq, Ne]

theorem not_lt : Autosimp.Statement.not_lt := by
  intro a b; cases a <;> cases b <;> simp [Not, Lt, Le, Ge]
  split_ifs <;> simp_all [and_comm]

theorem not_le : Autosimp.Statement.not_le := by
  intro a b; cases a <;> cases b <;> simp [Not, Lt, Le, Gt]
  split_ifs <;> simp_all [and_comm]

theorem not_gt : Autosimp.Statement.not_gt := by
  intro a b; cases a <;> cases b <;> simp [Not, Lt, Le, Gt]
  split_ifs <;> simp_all [and_comm]

theorem not_ge : Autosimp.Statement.not_ge := by
  intro a b; cases a <;> cases b <;> simp [Not, Lt, Le, Ge]
  split_ifs <;> simp_all [and_comm]

private theorem real_of_holds {z : ℂ} (h : Holds (Eq (re (some z)) (some z))) : z.im = 0 := by
  have : (z.re : ℂ) = z := by simpa [Eq, re, Holds] using h
  rw [← this]; simp

theorem and_unordered : Statement.and_unordered := by
  intro xs ys h
  have e : ∀ a, a ∈ xs ↔ a ∈ ys := fun _ => h.mem_iff
  unfold And; split_ifs <;> simp_all

theorem or_unordered : Statement.or_unordered := by
  intro xs ys h
  have e : ∀ a, a ∈ xs ↔ a ∈ ys := fun _ => h.mem_iff
  unfold Or; split_ifs <;> simp_all

private theorem and_congr_mem {l m : List Boolean}
    (hF : (∃ p, some p ∈ l ∧ ¬p) ↔ (∃ p, some p ∈ m ∧ ¬p)) (hN : none ∈ l ↔ none ∈ m) :
    And l = And m := by
  unfold And; split_ifs <;> simp_all

private theorem or_congr_mem {l m : List Boolean}
    (hF : (∃ p, some p ∈ l ∧ p) ↔ (∃ p, some p ∈ m ∧ p)) (hN : none ∈ l ↔ none ∈ m) :
    Or l = Or m := by
  unfold Or; split_ifs <;> simp_all

theorem and_flat : Statement.and_flat := by
  intro xs ys zs
  by_cases hF : ∃ p, some p ∈ ys ∧ ¬p
  · have hA : And ys = some False := by simp only [And, hF, ↓reduceIte]
    rw [hA]
    obtain ⟨p, hp, hn⟩ := hF
    have h1 : ∃ p, some p ∈ xs ++ some False :: zs ∧ ¬p := ⟨False, by simp, id⟩
    have h2 : ∃ p, some p ∈ xs ++ ys ++ zs ∧ ¬p := ⟨p, by simp [hp], hn⟩
    simp only [And, h1, h2, ↓reduceIte]
  · by_cases hN : none ∈ ys
    · have hA : And ys = none := by simp only [And, hF, hN, ↓reduceIte]
      rw [hA]
      apply and_congr_mem
      · simp only [List.mem_append, List.mem_cons, reduceCtorEq, false_or]
        constructor
        · rintro ⟨p, hp | hp, hn⟩
          · exact ⟨p, Or.inl (Or.inl hp), hn⟩
          · exact ⟨p, Or.inr hp, hn⟩
        · rintro ⟨p, (hp | hp) | hp, hn⟩
          · exact ⟨p, Or.inl hp, hn⟩
          · exact absurd ⟨p, hp, hn⟩ hF
          · exact ⟨p, Or.inr hp, hn⟩
      · simp [hN]
    · have hA : And ys = some True := by simp only [And, hF, hN, ↓reduceIte]
      rw [hA]
      apply and_congr_mem
      · simp only [List.mem_append, List.mem_cons, Option.some.injEq]
        constructor
        · rintro ⟨p, hp | hp | hp, hn⟩
          · exact ⟨p, Or.inl (Or.inl hp), hn⟩
          · exact absurd (hp ▸ trivial) hn
          · exact ⟨p, Or.inr hp, hn⟩
        · rintro ⟨p, (hp | hp) | hp, hn⟩
          · exact ⟨p, Or.inl hp, hn⟩
          · exact absurd ⟨p, hp, hn⟩ hF
          · exact ⟨p, Or.inr (Or.inr hp), hn⟩
      · simp [hN]

theorem or_flat : Statement.or_flat := by
  intro xs ys zs
  by_cases hF : ∃ p, some p ∈ ys ∧ p
  · have hA : Or ys = some True := by simp only [Or, hF, ↓reduceIte]
    rw [hA]
    obtain ⟨p, hp, hn⟩ := hF
    have h1 : ∃ p, some p ∈ xs ++ some True :: zs ∧ p := ⟨True, by simp, trivial⟩
    have h2 : ∃ p, some p ∈ xs ++ ys ++ zs ∧ p := ⟨p, by simp [hp], hn⟩
    simp only [Or, h1, h2, ↓reduceIte]
  · by_cases hN : none ∈ ys
    · have hA : Or ys = none := by simp only [Or, hF, hN, ↓reduceIte]
      rw [hA]
      apply or_congr_mem
      · simp only [List.mem_append, List.mem_cons, reduceCtorEq, false_or]
        constructor
        · rintro ⟨p, hp | hp, hn⟩
          · exact ⟨p, Or.inl (Or.inl hp), hn⟩
          · exact ⟨p, Or.inr hp, hn⟩
        · rintro ⟨p, (hp | hp) | hp, hn⟩
          · exact ⟨p, Or.inl hp, hn⟩
          · exact absurd ⟨p, hp, hn⟩ hF
          · exact ⟨p, Or.inr hp, hn⟩
      · simp [hN]
    · have hA : Or ys = some False := by simp only [Or, hF, hN, ↓reduceIte]
      rw [hA]
      apply or_congr_mem
      · simp only [List.mem_append, List.mem_cons, Option.some.injEq]
        constructor
        · rintro ⟨p, hp | hp | hp, hn⟩
          · exact ⟨p, Or.inl (Or.inl hp), hn⟩
          · exact (hp ▸ hn).elim
          · exact ⟨p, Or.inr hp, hn⟩
        · rintro ⟨p, (hp | hp) | hp, hn⟩
          · exact ⟨p, Or.inl hp, hn⟩
          · exact absurd ⟨p, hp, hn⟩ hF
          · exact ⟨p, Or.inr (Or.inr hp), hn⟩
      · simp [hN]

end Nary.LogicRules
