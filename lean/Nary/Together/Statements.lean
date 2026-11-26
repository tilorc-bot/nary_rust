import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Together.Statement

abbrev together_same_denominator : Prop :=
  ∀ (b n : Nary.Number) (cs ds : List Nary.Number), Nary.Holds (Nary.Lt n (Nary.lit 0)) → Nary.Add [Nary.Mul ([Nary.Pow b n] ++ cs), Nary.Mul ([Nary.Pow b n] ++ ds)] = Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul ds], Nary.Pow b n]

abbrev together_denominator : Prop :=
  ∀ (b n c : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.Lt n (Nary.lit 0)) → Nary.Add [Nary.Mul ([Nary.Pow b n] ++ cs), c] = Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.Pow b (Nary.Mul [Nary.lit (-1), n]), c]], Nary.Pow b n]

end Nary.Together.Statement
