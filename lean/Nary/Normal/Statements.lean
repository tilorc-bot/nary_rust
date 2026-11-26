import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Normal.Statement

abbrev collect_terms : Prop :=
  ∀ (a x b : Nary.Number), Nary.Add [Nary.Mul [a, x], Nary.Mul [b, x]] = Nary.Mul [Nary.Add [a, b], x]

abbrev add_zero : Prop :=
  ∀ (x : Nary.Number), Nary.Add [x, Nary.lit 0] = x

abbrev mul_one : Prop :=
  ∀ (x : Nary.Number), Nary.Mul [x, Nary.lit 1] = x

abbrev mul_zero : Prop :=
  ∀ (x : Nary.Number), x ≠ none → Nary.Mul [x, Nary.lit 0] = Nary.lit 0

abbrev distribute : Prop :=
  ∀ (a x y : Nary.Number), Nary.Mul [a, Nary.Add [x, y]] = Nary.Add [Nary.Mul [a, x], Nary.Mul [a, y]]

abbrev collect_powers : Prop :=
  ∀ (x a b : Nary.Number), Nary.Holds (Nary.Ne x (Nary.lit 0)) → Nary.Mul [Nary.Pow x a, Nary.Pow x b] = Nary.Pow x (Nary.Add [a, b])

abbrev collect_positive_powers : Prop :=
  ∀ (x a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.re a) (Nary.lit 0), Nary.Gt (Nary.re b) (Nary.lit 0)]) → Nary.Mul [Nary.Pow x a, Nary.Pow x b] = Nary.Pow x (Nary.Add [a, b])

abbrev collect_parallel_powers : Prop :=
  ∀ (x a c : Nary.Number), Nary.Holds (Nary.Gt c (Nary.lit 0)) → Nary.Mul [Nary.Pow x a, Nary.Pow x (Nary.Mul [c, a])] = Nary.Pow x (Nary.Mul [Nary.Add [Nary.lit 1, c], a])

abbrev collect_negative_powers : Prop :=
  ∀ (x a b : Nary.Number), Nary.Holds (Nary.Lt (Nary.re (Nary.Add [a, b])) (Nary.lit 0)) → Nary.Mul [Nary.Pow x a, Nary.Pow x b] = Nary.Pow x (Nary.Add [a, b])

abbrev exp_product : Prop :=
  ∀ (a b : Nary.Number), Nary.Mul [Nary.exp a, Nary.exp b] = Nary.exp (Nary.Add [a, b])

abbrev combine_radicals : Prop :=
  ∀ (a c b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Gt b (Nary.lit 0)]) → Nary.Mul [Nary.Pow a c, Nary.Pow b c] = Nary.Pow (Nary.Mul [a, b]) c

abbrev split_exponent : Prop :=
  ∀ (b n x : Nary.Number), Nary.Holds (Nary.Ne b (Nary.lit 0)) → Nary.Pow b (Nary.Add [n, x]) = Nary.Mul [Nary.Pow b n, Nary.Pow b x]

abbrev zero_base : Prop :=
  ∀ (c x : Nary.Number), Nary.Holds (Nary.Gt c (Nary.lit 0)) → c ≠ none → Nary.Pow (Nary.lit 0) (Nary.Mul [c, x]) = Nary.Pow (Nary.lit 0) x

abbrev pow_one : Prop :=
  ∀ (x : Nary.Number), Nary.Pow x (Nary.lit 1) = x

abbrev pow_zero : Prop :=
  ∀ (x : Nary.Number), Nary.Holds (Nary.Ne x (Nary.lit 0)) → x ≠ none → Nary.Pow x (Nary.lit 0) = Nary.lit 1

abbrev mul_pow_integer : Prop :=
  ∀ (x y n : Nary.Number), Nary.Holds (Nary.Eq (Nary.exp (Nary.Mul [Nary.Mul [Nary.Mul [Nary.lit 2, Nary.pi], Nary.I], n])) (Nary.lit 1)) → Nary.Pow (Nary.Mul [x, y]) n = Nary.Mul [Nary.Pow x n, Nary.Pow y n]

abbrev pow_pow_positive_integer : Prop :=
  ∀ (x a n : Nary.Number), Nary.Holds (Nary.And [Nary.Eq (Nary.exp (Nary.Mul [Nary.Mul [Nary.Mul [Nary.lit 2, Nary.pi], Nary.I], n])) (Nary.lit 1), Nary.Gt n (Nary.lit 0)]) → Nary.Pow (Nary.Pow x a) n = Nary.Pow x (Nary.Mul [a, n])

abbrev pow_pow_integer : Prop :=
  ∀ (x a n : Nary.Number), Nary.Holds (Nary.And [Nary.Eq (Nary.exp (Nary.Mul [Nary.Mul [Nary.Mul [Nary.lit 2, Nary.pi], Nary.I], n])) (Nary.lit 1), Nary.Ne x (Nary.lit 0)]) → Nary.Pow (Nary.Pow x a) n = Nary.Pow x (Nary.Mul [a, n])

abbrev pow_pow_integer_positive_exponent : Prop :=
  ∀ (x a n : Nary.Number), Nary.Holds (Nary.And [Nary.Eq (Nary.exp (Nary.Mul [Nary.Mul [Nary.Mul [Nary.lit 2, Nary.pi], Nary.I], n])) (Nary.lit 1), Nary.Gt (Nary.re a) (Nary.lit 0)]) → Nary.Pow (Nary.Pow x a) n = Nary.Pow x (Nary.Mul [a, n])

abbrev pow_pow_fraction : Prop :=
  ∀ (x a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Lt a (Nary.lit 1)]) → Nary.Pow (Nary.Pow x a) b = Nary.Pow x (Nary.Mul [a, b])

abbrev pow_pow_negative_fraction : Prop :=
  ∀ (x a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit (-1)), Nary.Lt a (Nary.lit 0), Nary.Gt (Nary.re b) (Nary.lit 0)]) → Nary.Pow (Nary.Pow x a) b = Nary.Pow x (Nary.Mul [a, b])

abbrev pow_pow_fraction_nonzero : Prop :=
  ∀ (x a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit (-1)), Nary.Lt a (Nary.lit 1), Nary.Ne x (Nary.lit 0)]) → Nary.Pow (Nary.Pow x a) b = Nary.Pow x (Nary.Mul [a, b])

abbrev pow_pow_positive_base : Prop :=
  ∀ (x a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt x (Nary.lit 0), Nary.Eq (Nary.re a) a]) → Nary.Pow (Nary.Pow x a) b = Nary.Pow x (Nary.Mul [a, b])

abbrev exp_pow_integer : Prop :=
  ∀ (a n : Nary.Number), Nary.Holds (Nary.Eq (Nary.exp (Nary.Mul [Nary.Mul [Nary.Mul [Nary.lit 2, Nary.pi], Nary.I], n])) (Nary.lit 1)) → Nary.Pow (Nary.exp a) n = Nary.exp (Nary.Mul [n, a])

abbrev pow_positive_factor : Prop :=
  ∀ (c x a : Nary.Number), Nary.Holds (Nary.Gt c (Nary.lit 0)) → Nary.Pow (Nary.Mul [c, x]) a = Nary.Mul [Nary.Pow c a, Nary.Pow x a]

abbrev pow_reciprocal_negative : Prop :=
  ∀ (x c : Nary.Number), Nary.Holds (Nary.Lt x (Nary.lit 0)) → Nary.Pow (Nary.Pow x (Nary.lit (-1))) c = Nary.Mul [Nary.Pow (Nary.lit (-1)) c, Nary.Pow (Nary.Mul [Nary.lit (-1), x]) (Nary.Mul [Nary.lit (-1), c])]

end Nary.Normal.Statement
