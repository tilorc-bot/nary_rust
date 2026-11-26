import Nary.Normal
import Nary.Expand.Statements
import Nary.ExpandLog.Statements
import Nary.Logcombine.Statements
import Nary.ExpandTrig.Statements
import Nary.Trigsimp.Statements
import Nary.Together.Statements
import Nary.Powsimp.Statements

namespace Nary.Strategies

private theorem square (z : ℂ) : Pow (some z) (some 2) = some (z ^ 2) := by
  simpa [lit] using Literals.pow_integer z 2 (Or.inr (by norm_num))

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

theorem expand_square : Expand.Statement.expand_square := by
  intro a b
  have sq (z : ℂ) : Pow (some z) (lit 2) = some (z ^ 2) := by
    simpa using Literals.pow_integer z 2 (Or.inr (by norm_num))
  cases a with
  | none => cases b <;> simp [Add, Mul, Pow, withDomain₂]
  | some x =>
  cases b with
  | none => simp [Add, Mul, Pow, withDomain₂]
  | some y =>
  have hs : Add [some x, some y] = some (x + y) := by simp [Add]
  rw [hs, sq, sq, sq]
  simp [Add, Mul, lit]
  ring

theorem expand_log_product : ExpandLog.Statement.expand_log_product := by
  intro a b h
  simp only [holds_and, List.mem_cons, List.not_mem_nil, forall_eq_or_imp] at h
  obtain ⟨ha, hb, -⟩ := h
  obtain ⟨r, hr, rfl⟩ := ArithmeticRules.holds_pos ha
  obtain ⟨q, hq, rfl⟩ := ArithmeticRules.holds_pos hb
  exact log_mul_pos hr hq

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

theorem expand_trig_cos_double : ExpandTrig.Statement.expand_trig_cos_double := by
  intro a
  cases a with
  | none => simp [sin, cos, Mul, Add, Pow, withDomain₂]
  | some z => simp [sin, cos, Mul, Add, lit, square, Complex.cos_two_mul', sub_eq_add_neg]

theorem trigsimp_sin_double : Trigsimp.Statement.trigsimp_sin_double :=
  fun a => (expand_trig_sin_double a).symm

theorem trigsimp_cos_double : Trigsimp.Statement.trigsimp_cos_double :=
  fun a => (expand_trig_cos_double a).symm

theorem powsimp_exp : Powsimp.Statement.powsimp_exp := ArithmeticRules.exp_product

theorem powsimp_positive_base : Powsimp.Statement.powsimp_positive_base := by
  intro a c d h
  obtain ⟨r, hr, rfl⟩ := ArithmeticRules.holds_pos h
  apply Normal.collect_powers
  simpa [Ne, Holds, lit] using hr.ne'

private theorem inv (z : ℂ) : Pow (some z) (lit (-1)) = if z = 0 then none else some z⁻¹ := by
  split_ifs with hz
  · subst hz; exact Literals.pow_zero_nonpositive (-1) (by norm_num)
  · rw [Literals.pow_integer _ _ (Or.inl hz)]; simp

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

theorem together_fractions : Together.Statement.together_fractions := by
  intro a b c d
  cases a <;> cases c <;> cases b <;> cases d <;> try (simp [Add, Mul, Pow, withDomain₂]; done)
  rename_i x z u w
  have hm : Mul [some u, some w] = some (u * w) := by simp [Mul]
  rw [hm, inv, inv, inv]
  by_cases hu : u = 0 <;> by_cases hw : w = 0 <;> simp [hu, hw, Add, Mul]
  field_simp

end Nary.Strategies
