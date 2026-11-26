use std::cmp::Ordering;
use std::collections::HashMap;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

const LIMIT: i128 = 1 << 62;

#[derive(Debug)]
struct Overflow;

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
struct Q {
    n: i128,
    d: i128,
}

fn gcd(a: i128, b: i128) -> i128 {
    let (mut a, mut b) = (a.unsigned_abs(), b.unsigned_abs());
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a.max(1) as i128
}

impl Q {
    const ZERO: Q = Q { n: 0, d: 1 };
    const ONE: Q = Q { n: 1, d: 1 };

    fn new(n: i128, d: i128) -> Result<Q, Overflow> {
        let g = gcd(n, d) * d.signum();
        let (n, d) = (n / g, d / g);
        if n.abs() >= LIMIT || d >= LIMIT {
            return Err(Overflow);
        }
        Ok(Q { n, d })
    }

    fn add(self, o: Q) -> Result<Q, Overflow> {
        let g = gcd(self.d, o.d);
        Q::new(self.n * (o.d / g) + o.n * (self.d / g), self.d / g * o.d)
    }

    fn sub(self, o: Q) -> Result<Q, Overflow> {
        self.add(o.neg())
    }

    fn mul(self, o: Q) -> Result<Q, Overflow> {
        let (g, h) = (gcd(self.n, o.d), gcd(o.n, self.d));
        Q::new((self.n / g) * (o.n / h), (self.d / h) * (o.d / g))
    }

    fn div(self, o: Q) -> Result<Q, Overflow> {
        self.mul(Q::new(o.d, o.n)?)
    }

    fn neg(self) -> Q {
        Q { n: -self.n, d: self.d }
    }

    fn is_zero(self) -> bool {
        self.n == 0
    }
}

impl Ord for Q {
    fn cmp(&self, o: &Q) -> Ordering {
        (self.n * o.d).cmp(&(o.n * self.d))
    }
}

impl PartialOrd for Q {
    fn partial_cmp(&self, o: &Q) -> Option<Ordering> {
        Some(self.cmp(o))
    }
}

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
struct Value {
    real: Q,
    delta: Q,
}

impl Value {
    const ZERO: Value = Value { real: Q::ZERO, delta: Q::ZERO };

    fn add(self, o: Value) -> Result<Value, Overflow> {
        Ok(Value { real: self.real.add(o.real)?, delta: self.delta.add(o.delta)? })
    }

    fn sub(self, o: Value) -> Result<Value, Overflow> {
        Ok(Value { real: self.real.sub(o.real)?, delta: self.delta.sub(o.delta)? })
    }

    fn scale(self, c: Q) -> Result<Value, Overflow> {
        Ok(Value { real: self.real.mul(c)?, delta: self.delta.mul(c)? })
    }
}

type Row = Vec<(usize, Q)>;

fn combine(row: &Row, c: Q, other: &Row, skip: usize) -> Result<Row, Overflow> {
    let mut out = Vec::with_capacity(row.len() + other.len());
    let (mut i, mut j) = (0, 0);
    while i < row.len() || j < other.len() {
        let left = row.get(i).map_or(usize::MAX, |e| e.0);
        let right = other.get(j).map_or(usize::MAX, |e| e.0);
        if i < row.len() && left == skip {
            i += 1;
        } else if left < right {
            out.push(row[i]);
            i += 1;
        } else if right < left {
            out.push((right, other[j].1.mul(c)?));
            j += 1;
        } else {
            let sum = row[i].1.add(other[j].1.mul(c)?)?;
            if !sum.is_zero() {
                out.push((left, sum));
            }
            i += 1;
            j += 1;
        }
    }
    Ok(out)
}

fn coefficient(row: &Row, var: usize) -> Option<Q> {
    row.binary_search_by_key(&var, |e| e.0).ok().map(|i| row[i].1)
}

#[derive(Clone, Copy)]
enum Relation {
    Gt,
    Ge,
    Eq,
    Le,
    Lt,
    Ne,
}

impl Relation {
    fn parse(text: &str) -> PyResult<Relation> {
        Ok(match text {
            ">" => Relation::Gt,
            ">=" => Relation::Ge,
            "=" => Relation::Eq,
            "<=" => Relation::Le,
            "<" => Relation::Lt,
            "!=" => Relation::Ne,
            _ => return Err(PyValueError::new_err(format!("unknown relation {text:?}"))),
        })
    }

    fn flipped(self) -> Relation {
        match self {
            Relation::Gt => Relation::Lt,
            Relation::Ge => Relation::Le,
            Relation::Eq => Relation::Eq,
            Relation::Le => Relation::Ge,
            Relation::Lt => Relation::Gt,
            Relation::Ne => Relation::Ne,
        }
    }
}

struct Change {
    var: usize,
    lower: Option<Value>,
    upper: Option<Value>,
}

#[pyclass(module = "nary._core._simplex")]
#[derive(Default)]
pub struct Simplex {
    rows: Vec<Row>,
    basic: Vec<usize>,
    row_of: Vec<Option<usize>>,
    lower: Vec<Option<Value>>,
    upper: Vec<Option<Value>>,
    value: Vec<Value>,
    slacks: HashMap<Row, usize>,
    trail: Vec<Change>,
    disequalities: Vec<(usize, Q)>,
    frames: Vec<(usize, usize, bool)>,
    conflict: bool,
    broken: bool,
}

impl Simplex {
    fn new_var(&mut self) -> usize {
        self.row_of.push(None);
        self.lower.push(None);
        self.upper.push(None);
        self.value.push(Value::ZERO);
        self.value.len() - 1
    }

    fn form(&self, terms: &[(usize, i128, i128)]) -> Result<Row, Overflow> {
        let mut row: Row = Vec::with_capacity(terms.len());
        let mut sorted = terms.to_vec();
        sorted.sort_unstable_by_key(|t| t.0);
        for (var, n, d) in sorted {
            let c = Q::new(n, d)?;
            match row.last_mut() {
                Some(last) if last.0 == var => last.1 = last.1.add(c)?,
                _ => row.push((var, c)),
            }
        }
        row.retain(|e| !e.1.is_zero());
        Ok(row)
    }

    fn slack(&mut self, form: Row) -> Result<usize, Overflow> {
        if let Some(&s) = self.slacks.get(&form) {
            return Ok(s);
        }
        let mut row: Row = Vec::new();
        let mut value = Value::ZERO;
        for &(var, c) in &form {
            value = value.add(self.value[var].scale(c)?)?;
            row = match self.row_of[var] {
                Some(r) => combine(&row, c, &self.rows[r].clone(), usize::MAX)?,
                None => combine(&row, c, &vec![(var, Q::ONE)], usize::MAX)?,
            };
        }
        let s = self.new_var();
        self.value[s] = value;
        self.row_of[s] = Some(self.rows.len());
        self.rows.push(row);
        self.basic.push(s);
        self.slacks.insert(form, s);
        Ok(s)
    }

    fn record(&mut self, var: usize) {
        if !self.frames.is_empty() {
            self.trail.push(Change { var, lower: self.lower[var], upper: self.upper[var] });
        }
    }

    fn assert_upper(&mut self, var: usize, bound: Value) -> Result<(), Overflow> {
        if self.upper[var].is_some_and(|u| bound >= u) {
            return Ok(());
        }
        if self.lower[var].is_some_and(|l| bound < l) {
            self.conflict = true;
            return Ok(());
        }
        self.record(var);
        self.upper[var] = Some(bound);
        if self.row_of[var].is_none() && self.value[var] > bound {
            self.update(var, bound)?;
        }
        Ok(())
    }

    fn assert_lower(&mut self, var: usize, bound: Value) -> Result<(), Overflow> {
        if self.lower[var].is_some_and(|l| bound <= l) {
            return Ok(());
        }
        if self.upper[var].is_some_and(|u| bound > u) {
            self.conflict = true;
            return Ok(());
        }
        self.record(var);
        self.lower[var] = Some(bound);
        if self.row_of[var].is_none() && self.value[var] < bound {
            self.update(var, bound)?;
        }
        Ok(())
    }

    fn update(&mut self, var: usize, v: Value) -> Result<(), Overflow> {
        let change = v.sub(self.value[var])?;
        for r in 0..self.rows.len() {
            if let Some(a) = coefficient(&self.rows[r], var) {
                let b = self.basic[r];
                self.value[b] = self.value[b].add(change.scale(a)?)?;
            }
        }
        self.value[var] = v;
        Ok(())
    }

    fn pivot_and_update(&mut self, r: usize, var: usize, v: Value) -> Result<(), Overflow> {
        let b = self.basic[r];
        let a = coefficient(&self.rows[r], var).expect("pivot on a zero coefficient");
        let theta = v.sub(self.value[b])?.scale(Q::ONE.div(a)?)?;
        self.value[b] = v;
        self.value[var] = self.value[var].add(theta)?;
        for other in 0..self.rows.len() {
            if other != r {
                if let Some(c) = coefficient(&self.rows[other], var) {
                    let k = self.basic[other];
                    self.value[k] = self.value[k].add(theta.scale(c)?)?;
                }
            }
        }
        let inverse = Q::ONE.div(a)?;
        let mut solved: Row = vec![(b, inverse)];
        for &(k, c) in &self.rows[r] {
            if k != var {
                solved.push((k, c.mul(inverse)?.neg()));
            }
        }
        solved.sort_unstable_by_key(|e| e.0);
        for other in 0..self.rows.len() {
            if other != r {
                if let Some(c) = coefficient(&self.rows[other], var) {
                    self.rows[other] = combine(&self.rows[other], c, &solved, var)?;
                }
            }
        }
        self.rows[r] = solved;
        self.basic[r] = var;
        self.row_of[b] = None;
        self.row_of[var] = Some(r);
        Ok(())
    }

    fn violated(&self) -> Option<(usize, bool)> {
        let mut found: Option<(usize, usize, bool)> = None;
        for (r, &b) in self.basic.iter().enumerate() {
            let low = self.lower[b].is_some_and(|l| self.value[b] < l);
            let high = self.upper[b].is_some_and(|u| self.value[b] > u);
            if (low || high) && found.is_none_or(|f| b < f.1) {
                found = Some((r, b, low));
            }
        }
        found.map(|(r, _, low)| (r, low))
    }

    fn run(&mut self) -> Result<bool, Overflow> {
        while let Some((r, low)) = self.violated() {
            let b = self.basic[r];
            let entering = self.rows[r]
                .iter()
                .filter(|&&(k, a)| {
                    let increase = (a.n > 0) == low;
                    if increase {
                        self.upper[k].is_none_or(|u| self.value[k] < u)
                    } else {
                        self.lower[k].is_none_or(|l| self.value[k] > l)
                    }
                })
                .map(|e| e.0)
                .min();
            let Some(var) = entering else { return Ok(false) };
            let target = if low { self.lower[b] } else { self.upper[b] };
            self.pivot_and_update(r, var, target.expect("violated bound"))?;
        }
        Ok(true)
    }

    fn assert_form(&mut self, terms: &[(usize, i128, i128)], relation: Relation, constant: (i128, i128)) -> Result<(), Overflow> {
        let mut form = self.form(terms)?;
        let mut bound = Q::new(constant.0, constant.1)?.neg();
        let mut relation = relation;
        let Some(&(_, lead)) = form.first() else {
            let holds = match relation {
                Relation::Gt => bound.n < 0,
                Relation::Ge => bound.n <= 0,
                Relation::Eq => bound.n == 0,
                Relation::Le => bound.n >= 0,
                Relation::Lt => bound.n > 0,
                Relation::Ne => bound.n != 0,
            };
            self.conflict |= !holds;
            return Ok(());
        };
        for e in form.iter_mut() {
            e.1 = e.1.div(lead)?;
        }
        bound = bound.div(lead)?;
        if lead.n < 0 {
            relation = relation.flipped();
        }
        let var = if form.len() == 1 { form[0].0 } else { self.slack(form)? };
        let at = |delta: i128| Value { real: bound, delta: Q { n: delta, d: 1 } };
        match relation {
            Relation::Gt => self.assert_lower(var, at(1)),
            Relation::Ge => self.assert_lower(var, at(0)),
            Relation::Eq => {
                self.assert_lower(var, at(0))?;
                self.assert_upper(var, at(0))
            }
            Relation::Le => self.assert_upper(var, at(0)),
            Relation::Lt => self.assert_upper(var, at(-1)),
            Relation::Ne => {
                self.disequalities.push((var, bound));
                Ok(())
            }
        }
    }

    fn decide(&mut self) -> Result<bool, Overflow> {
        if self.conflict || !self.run()? {
            return Ok(false);
        }
        let candidates: Vec<(usize, Q)> = self
            .disequalities
            .iter()
            .copied()
            .filter(|&(var, k)| self.value[var] == Value { real: k, delta: Q::ZERO })
            .collect();
        for (var, k) in candidates {
            if !self.satisfiable_beside(var, k, Q::ONE)? && !self.satisfiable_beside(var, k, Q::ONE.neg())? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    fn satisfiable_beside(&mut self, var: usize, k: Q, side: Q) -> Result<bool, Overflow> {
        self.push();
        let bound = Value { real: k, delta: side };
        if side.n > 0 {
            self.assert_lower(var, bound)?;
        } else {
            self.assert_upper(var, bound)?;
        }
        let satisfiable = !self.conflict && self.run()?;
        self.pop();
        Ok(satisfiable)
    }
}

#[pymethods]
impl Simplex {
    #[new]
    fn py_new() -> Self {
        Simplex::default()
    }

    fn variable(&mut self) -> usize {
        self.new_var()
    }

    #[pyo3(name = "assert_")]
    fn py_assert(&mut self, terms: Vec<(usize, i128, i128)>, relation: &str, constant: (i128, i128)) -> PyResult<()> {
        let relation = Relation::parse(relation)?;
        if terms.iter().any(|t| t.0 >= self.value.len()) {
            return Err(PyValueError::new_err("unknown variable"));
        }
        if !self.broken && self.assert_form(&terms, relation, constant).is_err() {
            self.broken = true;
        }
        Ok(())
    }

    fn check(&mut self) -> bool {
        if self.broken {
            return true;
        }
        match self.decide() {
            Ok(sat) => sat,
            Err(Overflow) => {
                self.broken = true;
                true
            }
        }
    }

    fn push(&mut self) {
        self.frames.push((self.trail.len(), self.disequalities.len(), self.conflict));
    }

    fn pop(&mut self) {
        let (mark, disequalities, conflict) = self.frames.pop().expect("pop without push");
        self.disequalities.truncate(disequalities);
        while self.trail.len() > mark {
            let change = self.trail.pop().expect("trail entry");
            self.lower[change.var] = change.lower;
            self.upper[change.var] = change.upper;
        }
        self.conflict = conflict;
    }
}
