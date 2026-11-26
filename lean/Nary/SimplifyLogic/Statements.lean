import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.SimplifyLogic.Statement

abbrev to_nnf_not_and : Prop :=
  ∀ (p q : Nary.Boolean) (ps : List Nary.Boolean), Nary.Not (Nary.And ([p, q] ++ ps)) = Nary.Or [Nary.Not p, Nary.Not (Nary.And ([q] ++ ps))]

abbrev to_nnf_not_or : Prop :=
  ∀ (p q : Nary.Boolean) (ps : List Nary.Boolean), Nary.Not (Nary.Or ([p, q] ++ ps)) = Nary.And [Nary.Not p, Nary.Not (Nary.Or ([q] ++ ps))]

abbrev to_nnf_contradiction : Prop :=
  ∀ (p : Nary.Boolean), p ≠ none → Nary.And [p, Nary.Not p] = Nary.false

abbrev to_nnf_excluded_middle : Prop :=
  ∀ (p : Nary.Boolean), p ≠ none → Nary.Or [p, Nary.Not p] = Nary.true

abbrev simplify_logic_and_absorption : Prop :=
  ∀ (p : Nary.Boolean) (ps : List Nary.Boolean), (∀ x ∈ ps, x ≠ none) → Nary.And [p, Nary.Or ([p] ++ ps)] = p

abbrev simplify_logic_or_absorption : Prop :=
  ∀ (p : Nary.Boolean) (ps : List Nary.Boolean), (∀ x ∈ ps, x ≠ none) → Nary.Or [p, Nary.And ([p] ++ ps)] = p

end Nary.SimplifyLogic.Statement
