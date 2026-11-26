import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.LogicRules.Statement

abbrev eq_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Eq a b) → a ≠ none → b ≠ none → Nary.Eq a b = Nary.true

abbrev eq_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Ne a b) → a ≠ none → b ≠ none → Nary.Eq a b = Nary.false

abbrev ne_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Ne a b) → a ≠ none → b ≠ none → Nary.Ne a b = Nary.true

abbrev ne_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Eq a b) → a ≠ none → b ≠ none → Nary.Ne a b = Nary.false

abbrev lt_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Lt a b) → a ≠ none → b ≠ none → Nary.Lt a b = Nary.true

abbrev lt_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Ge a b) → a ≠ none → b ≠ none → Nary.Lt a b = Nary.false

abbrev le_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Le a b) → a ≠ none → b ≠ none → Nary.Le a b = Nary.true

abbrev le_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Gt a b) → a ≠ none → b ≠ none → Nary.Le a b = Nary.false

abbrev gt_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Gt a b) → a ≠ none → b ≠ none → Nary.Gt a b = Nary.true

abbrev gt_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Le a b) → a ≠ none → b ≠ none → Nary.Gt a b = Nary.false

abbrev ge_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Ge a b) → a ≠ none → b ≠ none → Nary.Ge a b = Nary.true

abbrev ge_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Lt a b) → a ≠ none → b ≠ none → Nary.Ge a b = Nary.false

abbrev and_unordered : Prop :=
  Nary.Unordered Nary.And

abbrev and_flat : Prop :=
  Nary.Flat Nary.And

abbrev or_unordered : Prop :=
  Nary.Unordered Nary.Or

abbrev or_flat : Prop :=
  Nary.Flat Nary.Or

end Nary.LogicRules.Statement
