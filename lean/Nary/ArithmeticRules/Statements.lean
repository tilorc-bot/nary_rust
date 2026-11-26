import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ArithmeticRules.Statement

abbrev add_identity : Prop :=
  ∀ (a : Nary.Number), Nary.Add [a, Nary.lit 0] = a

abbrev add_self : Prop :=
  ∀ (a : Nary.Number), Nary.Add [a, a] = Nary.Mul [Nary.lit 2, a]

abbrev add_inverse : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Add [a, Nary.Mul [Nary.lit (-1), a]] = Nary.lit 0

abbrev mul_identity : Prop :=
  ∀ (a : Nary.Number), Nary.Mul [a, Nary.lit 1] = a

abbrev mul_absorbing : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Mul [a, Nary.lit 0] = Nary.lit 0

abbrev mul_inverse : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → a ≠ none → Nary.Mul [a, Nary.Pow a (Nary.lit (-1))] = Nary.lit 1

abbrev pow_one : Prop :=
  ∀ (a : Nary.Number), Nary.Pow a (Nary.lit 1) = a

abbrev pow_zero : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → a ≠ none → Nary.Pow a (Nary.lit 0) = Nary.lit 1

abbrev exp_log : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → Nary.exp (Nary.log a) = a

abbrev add_unordered : Prop :=
  Nary.Unordered Nary.Add

abbrev add_flat : Prop :=
  Nary.Flat Nary.Add

abbrev mul_unordered : Prop :=
  Nary.Unordered Nary.Mul

abbrev mul_flat : Prop :=
  Nary.Flat Nary.Mul

end Nary.ArithmeticRules.Statement
