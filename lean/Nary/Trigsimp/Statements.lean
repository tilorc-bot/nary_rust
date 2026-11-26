import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Trigsimp.Statement

abbrev trigsimp_sin_double : Prop :=
  ∀ (a : Nary.Number), Nary.Mul [Nary.lit 2, Nary.sin a, Nary.cos a] = Nary.sin (Nary.Mul [Nary.lit 2, a])

abbrev trigsimp_cos_double : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.Pow (Nary.cos a) (Nary.lit 2), Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.sin a) (Nary.lit 2)]] = Nary.cos (Nary.Mul [Nary.lit 2, a])

abbrev trigsimp_tan_squared : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.Pow (Nary.tan a) (Nary.lit 2), Nary.lit 1] = Nary.Pow (Nary.cos a) (Nary.lit (-2))

end Nary.Trigsimp.Statement
