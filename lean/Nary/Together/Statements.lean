import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Together.Statement

abbrev together_fractions : Prop :=
  ∀ (a b c d : Nary.Number), Nary.Add [Nary.Mul [a, Nary.Pow b (Nary.lit (-1))], Nary.Mul [c, Nary.Pow d (Nary.lit (-1))]] = Nary.Mul [Nary.Add [Nary.Mul [a, d], Nary.Mul [b, c]], Nary.Pow (Nary.Mul [b, d]) (Nary.lit (-1))]

end Nary.Together.Statement
