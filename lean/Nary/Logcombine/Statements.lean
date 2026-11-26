import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Logcombine.Statement

abbrev logcombine_coefficient : Prop :=
  ∀ (c a : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Gt c (Nary.lit 0)]) → Nary.Mul [c, Nary.log a] = Nary.log (Nary.Pow a c)

abbrev logcombine_negative_coefficient : Prop :=
  ∀ (c a : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Lt c (Nary.lit 0), Nary.Ne c (Nary.lit (-1))]) → Nary.Mul [c, Nary.log a] = Nary.Mul [Nary.lit (-1), Nary.log (Nary.Pow a (Nary.Mul [Nary.lit (-1), c]))]

abbrev logcombine_negative_power : Prop :=
  ∀ (a c : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Lt c (Nary.lit 0)]) → Nary.log (Nary.Pow a c) = Nary.Mul [Nary.lit (-1), Nary.log (Nary.Pow a (Nary.Mul [Nary.lit (-1), c]))]

abbrev logcombine_sum : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Gt b (Nary.lit 0)]) → Nary.Add [Nary.log a, Nary.log b] = Nary.log (Nary.Mul [a, b])

abbrev logcombine_difference : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Gt b (Nary.lit 0)]) → Nary.Add [Nary.log a, Nary.Mul [Nary.lit (-1), Nary.log b]] = Nary.log (Nary.Mul [a, Nary.Pow b (Nary.lit (-1))])

abbrev logcombine_negative_sum : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Gt b (Nary.lit 0)]) → Nary.Add [Nary.Mul [Nary.lit (-1), Nary.log a], Nary.Mul [Nary.lit (-1), Nary.log b]] = Nary.Mul [Nary.lit (-1), Nary.log (Nary.Mul [a, b])]

end Nary.Logcombine.Statement
