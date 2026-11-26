import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ArithmeticRules.Statement

abbrev add_identity : Prop :=
  ∀ (a : Nary.Number), Nary.Add [a, Nary.lit 0] = a

abbrev add_inverse : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Add [a, Nary.Mul [Nary.lit (-1), a]] = Nary.lit 0

abbrev mul_identity : Prop :=
  ∀ (a : Nary.Number), Nary.Mul [a, Nary.lit 1] = a

abbrev mul_absorbing : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Mul [a, Nary.lit 0] = Nary.lit 0

abbrev mul_inverse : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → a ≠ none → Nary.Mul [a, Nary.Pow a (Nary.lit (-1))] = Nary.lit 1

abbrev pow_right_identity : Prop :=
  ∀ (a : Nary.Number), Nary.Pow a (Nary.lit 1) = a

abbrev pow_left_absorbing : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Pow (Nary.lit 1) a = Nary.lit 1

abbrev add_unordered : Prop :=
  Nary.Unordered Nary.Add

abbrev add_flat : Prop :=
  Nary.Flat Nary.Add

abbrev mul_unordered : Prop :=
  Nary.Unordered Nary.Mul

abbrev mul_flat : Prop :=
  Nary.Flat Nary.Mul

end Nary.ArithmeticRules.Statement

namespace Nary.ArithmeticRules

structure Proved : Prop where
  add_identity : Statement.add_identity
  add_inverse : Statement.add_inverse
  mul_identity : Statement.mul_identity
  mul_absorbing : Statement.mul_absorbing
  mul_inverse : Statement.mul_inverse
  pow_right_identity : Statement.pow_right_identity
  pow_left_absorbing : Statement.pow_left_absorbing
  add_unordered : Statement.add_unordered
  add_flat : Statement.add_flat
  mul_unordered : Statement.mul_unordered
  mul_flat : Statement.mul_flat

end Nary.ArithmeticRules
