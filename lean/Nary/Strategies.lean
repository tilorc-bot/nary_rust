import Nary.ArithmeticRules
import Nary.Literals
import Nary.Expand.Statements
import Nary.ExpandLog.Statements
import Nary.Logcombine.Statements
import Nary.ExpandTrig.Statements
import Nary.Trigsimp.Statements
import Nary.Together.Statements
import Nary.Powsimp.Statements

namespace Nary.Strategies

private theorem log_mul_pos {r q : ℝ} (hr : 0 < r) (hq : 0 < q) :
    log (Mul [some (r : ℂ), some (q : ℂ)]) = Add [log (some (r : ℂ)), log (some (q : ℂ))] := by
  have h1 : (r : ℂ) ≠ 0 := by exact_mod_cast hr.ne'
  have h2 : (q : ℂ) ≠ 0 := by exact_mod_cast hq.ne'
  simp [log, withDomain, logDomain, Mul, Add, h1, h2, Complex.log_ofReal_mul hr h2,
    ArithmeticRules.log_real_pos hr]

theorem expand_distribute : Expand.Statement.expand_distribute := by
  intro a b c cs
  cases a <;> cases b <;> cases c <;> cases h : cs.mapM id <;>
    simp [Mul, Add, List.mapM_cons, h, mul_add]

theorem logcombine_sum : Logcombine.Statement.logcombine_sum := by
  intro a b h
  simp only [holds_and, List.mem_cons, List.not_mem_nil, forall_eq_or_imp] at h
  obtain ⟨ha, hb, -⟩ := h
  obtain ⟨r, hr, rfl⟩ := ArithmeticRules.holds_pos ha
  obtain ⟨q, hq, rfl⟩ := ArithmeticRules.holds_pos hb
  exact (log_mul_pos hr hq).symm

theorem expand_trig_sin_double : ExpandTrig.Statement.expand_trig_sin_double := by
  intro a
  cases a <;> simp [sin, cos, Mul, lit, Complex.sin_two_mul, mul_assoc]

theorem powsimp_exp : Powsimp.Statement.powsimp_exp := by
  intro a b; cases a <;> cases b <;> simp [exp, Mul, Add, Complex.exp_add]

theorem powsimp_positive_base : Powsimp.Statement.powsimp_positive_base := by
  intro a c d h
  obtain ⟨r, hr, rfl⟩ := ArithmeticRules.holds_pos h
  have hz : (r : ℂ) ≠ 0 := by exact_mod_cast hr.ne'
  cases c <;> cases d <;>
    simp [Pow, Mul, Add, withDomain₂, powDomain, powTotal, hz, add_mul, Complex.exp_add]

theorem trigsimp_tan_squared : Trigsimp.Statement.trigsimp_tan_squared := by
  intro a
  cases a with
  | none => simp [tan, withDomain, cos, Pow, withDomain₂, Add]
  | some z =>
  by_cases hc : Complex.cos z = 0
  · rw [cos, Option.map_some, hc, Literals.pow_zero_nonpositive (-2) (by norm_num)]
    simp [tan, withDomain, tanDomain, hc, Pow, withDomain₂, Add]
  · have ht : tan (some z) = some (Complex.tan z) := by simp [tan, withDomain, tanDomain, hc]
    rw [cos, Option.map_some, Literals.pow_integer _ _ (Or.inl hc), ht,
      Literals.pow_integer _ _ (Or.inr (by norm_num))]
    simp [Add, lit, Complex.tan_eq_sin_div_cos]
    field_simp
    linear_combination Complex.sin_sq_add_cos_sq z

end Nary.Strategies
