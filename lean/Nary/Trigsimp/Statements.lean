import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Trigsimp.Statement

abbrev trigsimp_sin_double : Prop :=
  ∀ (a : Nary.Number), Nary.Mul [Nary.sin a, Nary.cos a] = Nary.Mul [Nary.sin (Nary.Mul [Nary.lit 2, a]), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]

abbrev trigsimp_cos_double : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.Pow (Nary.cos a) (Nary.lit 2), Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.sin a) (Nary.lit 2)]] = Nary.cos (Nary.Mul [Nary.lit 2, a])

abbrev trigsimp_cos_double_cos : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.Mul [Nary.lit 2, Nary.Pow (Nary.cos a) (Nary.lit 2)], Nary.lit (-1)] = Nary.cos (Nary.Mul [Nary.lit 2, a])

abbrev trigsimp_cos_double_sin : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-2), Nary.Pow (Nary.sin a) (Nary.lit 2)]] = Nary.cos (Nary.Mul [Nary.lit 2, a])

abbrev trigsimp_tan_squared : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.Pow (Nary.tan a) (Nary.lit 2), Nary.lit 1] = Nary.Pow (Nary.cos a) (Nary.lit (-2))

abbrev trigsimp_secant_squared : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.Pow (Nary.cos a) (Nary.lit (-2)), Nary.lit (-1)] = Nary.Pow (Nary.tan a) (Nary.lit 2)

abbrev trigsimp_tan_power : Prop :=
  ∀ (a n : Nary.Number), Nary.Holds (Nary.And [Nary.Eq (Nary.exp (Nary.Mul [Nary.Mul [Nary.Mul [Nary.lit 2, Nary.pi], Nary.I], n])) (Nary.lit 1), Nary.Gt n (Nary.lit 0)]) → Nary.Mul [Nary.Pow (Nary.sin a) n, Nary.Pow (Nary.cos a) (Nary.Mul [Nary.lit (-1), n])] = Nary.Pow (Nary.tan a) n

abbrev trigsimp_sin_sum : Prop :=
  ∀ (a b : Nary.Number), Nary.Add [Nary.Mul [Nary.sin a, Nary.cos b], Nary.Mul [Nary.sin b, Nary.cos a]] = Nary.sin (Nary.Add [a, b])

abbrev trigsimp_cos_sum : Prop :=
  ∀ (a b : Nary.Number), Nary.Add [Nary.Mul [Nary.cos a, Nary.cos b], Nary.Mul [Nary.lit (-1), Nary.sin a, Nary.sin b]] = Nary.cos (Nary.Add [a, b])

end Nary.Trigsimp.Statement
