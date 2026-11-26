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

abbrev mul_repeats : Prop :=
  ∀ (a : Nary.Number), Nary.Mul [a, a] = Nary.Pow a (Nary.lit 2)

abbrev mul_inverse : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → a ≠ none → Nary.Mul [a, Nary.Pow a (Nary.lit (-1))] = Nary.lit 1

abbrev add_flat : Prop :=
  Nary.Flat Nary.Add

abbrev add_unordered : Prop :=
  Nary.Unordered Nary.Add

abbrev add_identity_law : Prop :=
  Nary.Identity Nary.Add (Nary.lit 0)

abbrev add_repeats_law : Prop :=
  Nary.Repeats Nary.Add (fun a n => Nary.Mul [n, a])

abbrev mul_flat : Prop :=
  Nary.Flat Nary.Mul

abbrev mul_unordered : Prop :=
  Nary.Unordered Nary.Mul

abbrev mul_identity_law : Prop :=
  Nary.Identity Nary.Mul (Nary.lit 1)

abbrev mul_absorbing_law : Prop :=
  Nary.Absorbing Nary.Mul (Nary.lit 0)

abbrev mul_repeats_law : Prop :=
  Nary.Repeats Nary.Mul (fun a n => Nary.Pow a n)

abbrev and_flat : Prop :=
  Nary.Flat Nary.And

abbrev and_unordered : Prop :=
  Nary.Unordered Nary.And

abbrev and_identity_law : Prop :=
  Nary.Identity Nary.And Nary.true

abbrev and_absorbing_law : Prop :=
  Nary.Absorbing Nary.And Nary.false

abbrev and_idempotent_law : Prop :=
  Nary.Idempotent Nary.And

abbrev or_flat : Prop :=
  Nary.Flat Nary.Or

abbrev or_unordered : Prop :=
  Nary.Unordered Nary.Or

abbrev or_identity_law : Prop :=
  Nary.Identity Nary.Or Nary.false

abbrev or_absorbing_law : Prop :=
  Nary.Absorbing Nary.Or Nary.true

abbrev or_idempotent_law : Prop :=
  Nary.Idempotent Nary.Or

abbrev not_involution_law : Prop :=
  Nary.Involution Nary.Not

end Nary.ArithmeticRules.Statement

namespace Nary.ArithmeticRules

structure Proved : Prop where
  add_identity : Statement.add_identity
  add_self : Statement.add_self
  add_inverse : Statement.add_inverse
  mul_identity : Statement.mul_identity
  mul_absorbing : Statement.mul_absorbing
  mul_repeats : Statement.mul_repeats
  mul_inverse : Statement.mul_inverse
  add_flat : Statement.add_flat
  add_unordered : Statement.add_unordered
  add_identity_law : Statement.add_identity_law
  add_repeats_law : Statement.add_repeats_law
  mul_flat : Statement.mul_flat
  mul_unordered : Statement.mul_unordered
  mul_identity_law : Statement.mul_identity_law
  mul_absorbing_law : Statement.mul_absorbing_law
  mul_repeats_law : Statement.mul_repeats_law
  and_flat : Statement.and_flat
  and_unordered : Statement.and_unordered
  and_identity_law : Statement.and_identity_law
  and_absorbing_law : Statement.and_absorbing_law
  and_idempotent_law : Statement.and_idempotent_law
  or_flat : Statement.or_flat
  or_unordered : Statement.or_unordered
  or_identity_law : Statement.or_identity_law
  or_absorbing_law : Statement.or_absorbing_law
  or_idempotent_law : Statement.or_idempotent_law
  not_involution_law : Statement.not_involution_law

end Nary.ArithmeticRules
