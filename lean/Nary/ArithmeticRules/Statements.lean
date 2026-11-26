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

abbrev add_self_law : Prop :=
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

abbrev pow_whole_split_law : Prop :=
  ∀ (n : Nary.Number), Nary.Maps (fun a => Nary.Pow a n) Nary.Mul Nary.Mul (fun a => Nary.Holds (Nary.Eq (Nary.exp (Nary.Mul [Nary.lit 2, Nary.pi, Nary.I, n])) (Nary.lit 1)))

abbrev pow_positive_split_law : Prop :=
  ∀ (n : Nary.Number), Nary.Maps (fun a => Nary.Pow a n) Nary.Mul Nary.Mul (fun a => Nary.Holds (Nary.Gt a (Nary.lit 0)))

abbrev pow_composes_law : Prop :=
  Nary.Composes (fun a n => Nary.Pow a n) Nary.Mul (fun a n => Nary.Holds (Nary.Eq (Nary.exp (Nary.Mul [Nary.lit 2, Nary.pi, Nary.I, n])) (Nary.lit 1)))

abbrev exp_maps_law : Prop :=
  Nary.Maps (fun a => Nary.exp a) Nary.Add Nary.Mul (fun _ => True)

abbrev exp_periodic_law : Prop :=
  Nary.Maps₁ (fun a => Nary.exp a) (fun a => Nary.Add [a, Nary.Mul [Nary.lit 2, Nary.pi, Nary.I]]) (fun a => a)

abbrev exp_undoes_law : Prop :=
  Nary.Undoes (fun a => Nary.exp a) (fun a => Nary.log a) (fun _ => True)

abbrev log_maps_law : Prop :=
  Nary.Maps (fun a => Nary.log a) Nary.Mul Nary.Add (fun a => Nary.Holds (Nary.Gt a (Nary.lit 0)))

abbrev log_undoes_law : Prop :=
  Nary.Undoes (fun a => Nary.log a) (fun a => Nary.exp a) (fun a => Nary.Holds (Nary.And [Nary.Lt (Nary.Mul [Nary.lit (-1), Nary.pi]) (Nary.re (Nary.Mul [Nary.lit (-1), Nary.I, a])), Nary.Le (Nary.re (Nary.Mul [Nary.lit (-1), Nary.I, a])) Nary.pi]))

abbrev sin_odd_law : Prop :=
  Nary.Maps₁ (fun a => Nary.sin a) (fun a => Nary.Mul [Nary.lit (-1), a]) (fun a => Nary.Mul [Nary.lit (-1), a])

abbrev sin_antiperiodic_law : Prop :=
  Nary.Maps₁ (fun a => Nary.sin a) (fun a => Nary.Add [a, Nary.pi]) (fun a => Nary.Mul [Nary.lit (-1), a])

abbrev cos_even_law : Prop :=
  Nary.Maps₁ (fun a => Nary.cos a) (fun a => Nary.Mul [Nary.lit (-1), a]) (fun a => a)

abbrev cos_antiperiodic_law : Prop :=
  Nary.Maps₁ (fun a => Nary.cos a) (fun a => Nary.Add [a, Nary.pi]) (fun a => Nary.Mul [Nary.lit (-1), a])

abbrev tan_odd_law : Prop :=
  Nary.Maps₁ (fun a => Nary.tan a) (fun a => Nary.Mul [Nary.lit (-1), a]) (fun a => Nary.Mul [Nary.lit (-1), a])

abbrev tan_periodic_law : Prop :=
  Nary.Maps₁ (fun a => Nary.tan a) (fun a => Nary.Add [a, Nary.pi]) (fun a => a)

abbrev and_flat : Prop :=
  Nary.Flat Nary.And

abbrev and_unordered : Prop :=
  Nary.Unordered Nary.And

abbrev and_identity_law : Prop :=
  Nary.Identity Nary.And Nary.true

abbrev and_dominant_law : Prop :=
  Nary.Dominant Nary.And Nary.false

abbrev and_idempotent_law : Prop :=
  Nary.Idempotent Nary.And

abbrev or_flat : Prop :=
  Nary.Flat Nary.Or

abbrev or_unordered : Prop :=
  Nary.Unordered Nary.Or

abbrev or_identity_law : Prop :=
  Nary.Identity Nary.Or Nary.false

abbrev or_dominant_law : Prop :=
  Nary.Dominant Nary.Or Nary.true

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
  add_self_law : Statement.add_self_law
  mul_flat : Statement.mul_flat
  mul_unordered : Statement.mul_unordered
  mul_identity_law : Statement.mul_identity_law
  mul_absorbing_law : Statement.mul_absorbing_law
  mul_repeats_law : Statement.mul_repeats_law
  exp_maps_law : Statement.exp_maps_law
  exp_periodic_law : Statement.exp_periodic_law
  exp_undoes_law : Statement.exp_undoes_law
  log_maps_law : Statement.log_maps_law
  log_undoes_law : Statement.log_undoes_law
  sin_odd_law : Statement.sin_odd_law
  sin_antiperiodic_law : Statement.sin_antiperiodic_law
  cos_even_law : Statement.cos_even_law
  cos_antiperiodic_law : Statement.cos_antiperiodic_law
  tan_odd_law : Statement.tan_odd_law
  tan_periodic_law : Statement.tan_periodic_law
  and_flat : Statement.and_flat
  and_unordered : Statement.and_unordered
  and_identity_law : Statement.and_identity_law
  and_dominant_law : Statement.and_dominant_law
  and_idempotent_law : Statement.and_idempotent_law
  or_flat : Statement.or_flat
  or_unordered : Statement.or_unordered
  or_identity_law : Statement.or_identity_law
  or_dominant_law : Statement.or_dominant_law
  or_idempotent_law : Statement.or_idempotent_law
  not_involution_law : Statement.not_involution_law

structure Pending : Prop where
  pow_composes_law : Statement.pow_composes_law
  pow_positive_split_law : Statement.pow_positive_split_law
  pow_whole_split_law : Statement.pow_whole_split_law

end Nary.ArithmeticRules
