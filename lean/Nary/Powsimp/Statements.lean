import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Powsimp.Statement

abbrev powsimp_positive_base : Prop :=
  ∀ (a c d : Nary.Number), Nary.Holds (Nary.Gt a (Nary.lit 0)) → Nary.Mul [Nary.Pow a c, Nary.Pow a d] = Nary.Pow a (Nary.Add [c, d])

abbrev powsimp_exp : Prop :=
  ∀ (a b : Nary.Number), Nary.Mul [Nary.exp a, Nary.exp b] = Nary.exp (Nary.Add [a, b])

end Nary.Powsimp.Statement
