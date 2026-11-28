import argparse
import json
import random
import resource
import signal
import statistics
import sys
import time
from pathlib import Path


def nary_namespace():
    import nary
    from nary.logic import And, Or, true

    names = {name: getattr(nary, name) for name in nary.__all__}
    names.update(And=And, Or=Or, true=true)
    names.update({s: nary.NumberKind(s) for s in ("x", "y", "z", "w")})
    return names


def real(e):
    from nary import Eq, re

    return Eq(re(e), e)


def fact_sets(n):
    x, y, z = n["x"], n["y"], n["z"]
    Gt, Ge, Lt, Ne = n["Gt"], n["Ge"], n["Lt"], n["Ne"]
    return {
        "none": [],
        "x>0": [Gt(x, 0)],
        "x>0, y>0": [Gt(x, 0), Gt(y, 0)],
        "x, y real": [real(x), real(y)],
        "x!=0": [Ne(x, 0)],
        "x>1, y>x, z>=0": [Gt(x, 1), Gt(y, x), Ge(z, 0)],
        "x>0, y<0, z!=0": [Gt(x, 0), Lt(y, 0), Ne(z, 0)],
        "-1<x<1, y>2": [Gt(x, -1), Lt(x, 1), Gt(y, 2)],
    }


def corpus(n, count=40, seed=0):
    x, y, z = n["x"], n["y"], n["z"]
    exp, log, sin, cos, tan, Pow = n["exp"], n["log"], n["sin"], n["cos"], n["tan"], n["Pow"]
    half = Pow(2, -1)
    hand = [
        x / x, (x + 1) / (x + 1), x ** 0, log(x) * 0, exp(log(x)), exp(log(x + 1)), log(x * y),
        log(x ** 2), (x ** 2) ** half, x ** half * y ** half, (x * y) ** half, x ** y * x ** z,
        1 / x + 1 / y, log(exp(x)), tan(x) * cos(x), x * y / (x * y), (x ** 2 - 1) / (x - 1),
        log(x) / log(x), exp(x) / exp(x), sin(x) / sin(x), (x - y) / (x - y), log(x + y) * 0,
        log(x ** half), (x ** y) ** z, log(x ** y), 1 / (x * y + 1), (x + y) ** 0, x * log(y) * 0,
        exp(x) * exp(y), sin(x) ** 2 + cos(x) ** 2, log(1 + x ** 2), (1 - x) ** half,
    ]
    rng = random.Random(seed)
    leaves = [x, y, z, x, y, n["NumberKind"](1), n["NumberKind"](2), n["NumberKind"](-1), half]

    def grow(depth):
        if depth == 0 or rng.random() < 0.25:
            return rng.choice(leaves)
        op = rng.choice(["+", "*", "-", "/", "**", "exp", "log", "sin", "cos", "sqrt"])
        if op in ("exp", "log", "sin", "cos"):
            return {"exp": exp, "log": log, "sin": sin, "cos": cos}[op](grow(depth - 1))
        if op == "sqrt":
            return grow(depth - 1) ** half
        a, b = grow(depth - 1), grow(depth - 1)
        return {"+": a + b, "*": a * b, "-": a - b, "/": a / b, "**": a ** b}[op]

    return hand + [grow(3) for _ in range(count)]


def subterms(e):
    found = []
    stack = [e]
    while stack:
        t = stack.pop()
        if t.head is None and not t.is_symbol:
            continue
        if t not in found:
            found.append(t)
        stack.extend(t.args)
    return found


def rule_conditions(n, e):
    Mul, Pow, log, And, Ge, Gt, Ne = n["Mul"], n["Pow"], n["log"], n["And"], n["Ge"], n["Gt"], n["Ne"]
    half = Pow(2, -1)
    conditions = []
    for t in subterms(e):
        if t.head == Pow and t.args[1] == half and t.args[0].head == Pow and t.args[0].args[1] == 2:
            conditions.append(Ge(t.args[0].args[0], 0))
        if t.head == log and t.args[0].head == Mul:
            conditions.append(And(*(Gt(f, 0) for f in t.args[0].args)))
        if t.head == log and t.args[0].head == Pow:
            conditions.append(And(Gt(t.args[0].args[0], 0), real(t.args[0].args[1])))
        if t.head == Pow and t.args[0].head == Mul:
            conditions.append(And(*(Ge(f, 0) for f in t.args[0].args), real(t.args[1])))
        if t.head == Pow and t.args[0].head == Pow:
            conditions.append(And(Gt(t.args[0].args[0], 0), real(t.args[0].args[1])))
        if t.head == Mul and any(f.head == Pow and f.args[1] == -1 and f.args[0] in t.args for f in t.args):
            conditions.extend(Ne(f, 0) for f in t.args if Pow(f, -1) in t.args)
    return conditions


def bounds_and_chains(n):
    x, y, z, w = n["x"], n["y"], n["z"], n["w"]
    Gt, Ge, Lt, Le, Ne, Eq = n["Gt"], n["Ge"], n["Lt"], n["Le"], n["Ne"], n["Eq"]
    exp, log, sin, cos = n["exp"], n["log"], n["sin"], n["cos"]
    return [
        ("x>1, y>x, z>=0", [Gt(x, 1), Gt(y, x), Ge(z, 0)], [
            Gt(y, 1), Gt(x + y, 2), Gt(y + z, 1), Ne(y - 1, 0), Gt(2 * y - x, 1), Gt(log(y), 0),
            Gt(exp(y), 1), Gt(x * y, 0), Gt(y * z + x, 1), Ne(x * y, 0), Gt(x * y, 1), Gt(y, 2),
            Gt(exp(y), 2), Lt(z, 1), Ge(z * x, 0), Gt(log(x) + log(y), 0),
        ]),
        ("-1<x<1, y>2", [Gt(x, -1), Lt(x, 1), Gt(y, 2)], [
            Lt(x, 2), Gt(y - x, 1), Gt(y + x, 1), Ne(x - y, 0), Gt(sin(y) + y, 1), Gt(log(y), 0),
            Gt(log(y) + x, -1), Lt(exp(x), 1), Gt(y - x, 2), Ge(cos(x) + x, -2), Ne(x, 0),
            Gt(x * y, -3), Lt(x - 1, 0),
        ]),
        ("x, y real, x>=y", [real(x), real(y), Ge(x, y)], [
            Ge(x - y, 0), Le(y - x, 0), Ge(2 * x, 2 * y), Gt(exp(x) + exp(y), 0), Ge(cos(x) + 1, 0),
            Le(sin(x) - 1, 0), Ge(x ** 2, 0), Gt(x ** 2 + 1, 0), Ge(x ** 2 + y ** 2, 0), Gt(x, y),
            Ne(exp(x) - exp(y), 0), Gt(exp(x - y) + 1, 1),
        ]),
        ("x<y<z<w", [Lt(x, y), Lt(y, z), Lt(z, w)], [
            Lt(x, w), Ne(x, w), Lt(2 * x, y + z), Gt(w - x, 0), Lt(x + y, z + w), Lt(x + w, y + z),
            Gt(exp(w), exp(x)), Ge(w, y), Eq(x, x), Lt(x - w, y - z),
        ]),
    ]


def write_workload(path, cap):
    n = nary_namespace()
    from nary.arithmetic_rules import rules
    from nary.deciding import Facts
    from nary.rewriting import rewrite

    sets = fact_sets(n)
    rng = random.Random(1)
    categories = {"rewrite": [], "rule conditions": [], "subterms": []}
    for name, facts in sets.items():
        for e in corpus(n):
            known = Facts(facts)
            asked = []
            rewrite(e, rules, known=lambda c: asked.append(c) or known(c))
            categories["rewrite"] += [(name, c) for c in asked]
            categories["rule conditions"] += [(name, c) for c in rule_conditions(n, e)]
            for t in subterms(e):
                for q in (n["Gt"](t, 0), n["Lt"](t, 0), n["Ne"](t, 0), real(t)):
                    categories["subterms"].append((name, q))
    workload = {"facts": {name: [repr(f) for f in fs] for name, fs in sets.items()}, "questions": []}
    for category, pairs in categories.items():
        unique = list(dict.fromkeys((name, repr(c)) for name, c in pairs))
        for name, c in sorted(rng.sample(unique, min(cap, len(unique)))):
            workload["questions"].append([category, name, c])
    for name, facts, questions in bounds_and_chains(n):
        workload["facts"][name] = [repr(f) for f in facts]
        workload["questions"] += [["bounds and chains", name, repr(q)] for q in questions]
    Path(path).write_text(json.dumps(workload, indent=1))
    print(f"{len(workload['questions'])} questions")


class OutOfTime(Exception):
    pass


def timed(f, limit=None):
    if limit:
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(OutOfTime()))
        signal.setitimer(signal.ITIMER_REAL, limit)
    start = time.perf_counter_ns()
    try:
        result = f()
    except (OutOfTime, MemoryError, RecursionError):
        result = None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    return result, (time.perf_counter_ns() - start) / 1000


def grouped(workload):
    groups = {}
    for i, (category, name, text) in enumerate(workload["questions"]):
        groups.setdefault(name, []).append((i, text))
    return groups


def run_nary(workload, rounds):
    import nary.deciding as deciding

    n = nary_namespace()
    facts = {name: [eval(f, n) for f in fs] for name, fs in workload["facts"].items()}
    questions = [eval(text, n) for _, _, text in workload["questions"]]
    codes = [compile(text, "<q>", "eval") for _, _, text in workload["questions"]]
    count = len(questions)
    times = {key: [[] for _ in range(count)] for key in ("construct", "first", "repeat", "one-shot")}
    answers = [None] * count
    setup = {name: [] for name in facts}
    for _ in range(rounds):
        for i, code in enumerate(codes):
            times["construct"][i].append(timed(lambda: eval(code, n))[1])
        for name, items in grouped(workload).items():
            known, t = timed(lambda: deciding.Facts(facts[name]))
            setup[name].append(t)
            for i, _ in items:
                answers[i], t = timed(lambda: known(questions[i]))
                times["first"][i].append(t)
            for i, _ in items:
                times["repeat"][i].append(timed(lambda: known(questions[i]))[1])
            for i, _ in items:
                times["one-shot"][i].append(timed(lambda: deciding.Facts(facts[name])(questions[i]))[1])
    split = split_nary(workload, facts, questions)
    return {
        "answers": answers,
        "times": {key: [min(v) for v in values] for key, values in times.items()},
        "setup": {name: min(v) for name, v in setup.items()},
        "split": split,
    }


def split_nary(workload, facts, questions):
    import nary.deciding as deciding

    clock = {"solver": 0.0, "translate": 0.0, "depth": 0}

    class TimedSimplex:
        def __init__(self):
            self.inner = deciding_simplex()

        def __getattr__(self, name):
            method = getattr(self.inner, name)

            def call(*args):
                start = time.perf_counter_ns()
                result = method(*args)
                clock["solver"] += (time.perf_counter_ns() - start) / 1000
                return result

            return call

    def translating(method):
        def call(self, *args):
            if clock["depth"]:
                return method(self, *args)
            clock["depth"] += 1
            start = time.perf_counter_ns()
            try:
                return method(self, *args)
            finally:
                clock["translate"] += (time.perf_counter_ns() - start) / 1000
                clock["depth"] -= 1

        return call

    class TimedFacts(deciding.Facts):
        _linear = translating(deciding.Facts._linear)
        _difference = translating(deciding.Facts._difference)
        _encode = translating(deciding.Facts._encode)

    deciding_simplex = deciding.Simplex
    deciding.Simplex = TimedSimplex
    parts = []
    try:
        for name, items in grouped(workload).items():
            known = TimedFacts(facts[name])
            for i, _ in items:
                clock["solver"] = clock["translate"] = 0.0
                _, total = timed(lambda: known(questions[i]))
                parts.append((i, total, clock["solver"], clock["translate"]))
    finally:
        deciding.Simplex = deciding_simplex
    parts.sort()
    return [p[1:] for p in parts]


def run_properties(workload, rounds):
    from nary.properties import holds

    n = nary_namespace()
    facts = {name: frozenset(eval(f, n) for f in fs) for name, fs in workload["facts"].items()}
    questions = [(name, eval(text, n)) for _, name, text in workload["questions"]]
    times = [[] for _ in questions]
    answers = [None] * len(questions)
    for _ in range(rounds):
        for i, (name, q) in enumerate(questions):
            answers[i], t = timed(lambda: holds(q, facts[name]))
            times[i].append(t)
    return {"answers": answers, "times": {"one-shot": [min(v) for v in times]}}


def sympy_namespace(real_symbols, assumptions):
    import sympy

    names = {f: getattr(sympy, f) for f in ("Add", "Mul", "Pow", "exp", "log", "sin", "cos", "tan", "re", "pi", "E", "I")}
    for relation in ("Gt", "Ge", "Lt", "Le", "Eq", "Ne", "And", "Or"):
        names[relation] = lambda *args, relation=relation: (relation, *args)
    names["true"] = ("And",)
    for s in ("x", "y", "z", "w"):
        names[s] = sympy.Symbol(s, **assumptions.get(s, {"real": True} if s in real_symbols else {}))
    return names


LIMIT = 10

ORDER = {"Gt": ("gt", "positive"), "Ge": ("ge", "nonnegative"), "Lt": ("lt", "negative"), "Le": ("le", "nonpositive")}


def sympy_old(q):
    head, *args = q
    if head in ("And", "Or"):
        results = [sympy_old(a) for a in args]
        return all(results) if head == "And" else any(results)
    a, b = map(__import__("sympy").sympify, args)
    if head in ORDER:
        return getattr(a - b, "is_" + ORDER[head][1]) is True
    if head == "Ne":
        return (a - b).is_zero is False
    if head == "Eq" and a == b:
        return False
    if head == "Eq" and getattr(a, "func", None) is __import__("sympy").re:
        return b.is_real is True
    return (a - b).is_zero is True


def sympy_predicate(q):
    from sympy import And, Or, Q, re, sympify

    head, *args = q
    if head in ("And", "Or"):
        return (And if head == "And" else Or)(*(sympy_predicate(a) for a in args))
    a, b = map(sympify, args)
    if head in ORDER:
        relation, sign = ORDER[head]
        return getattr(Q, sign)(a) if b == 0 else getattr(Q, relation)(a, b)
    if head == "Ne":
        return ~Q.zero(a - b)
    if head == "Eq" and getattr(a, "func", None) is re:
        return Q.real(b)
    return Q.eq(a, b)


def old_assumptions(facts):
    from sympy import Symbol

    declared = {}
    for head, a, b in facts:
        if head == "Eq" and isinstance(b, Symbol):
            declared.setdefault(b.name, {})["real"] = True
            continue
        if not isinstance(a, Symbol):
            a, b = b, a
            head = {"Gt": "Lt", "Lt": "Gt", "Ge": "Le", "Le": "Ge"}.get(head, head)
        if not isinstance(a, Symbol):
            continue
        if isinstance(b, Symbol):
            declared.setdefault(a.name, {})["real"] = True
            declared.setdefault(b.name, {})["real"] = True
            continue
        key = {"Gt": "positive", "Ge": "nonnegative", "Lt": "negative", "Le": "nonpositive", "Ne": "zero"}[head]
        if head == "Ne":
            if b == 0:
                declared.setdefault(a.name, {})["zero"] = False
        elif (head in ("Gt", "Ge") and b >= 0) or (head in ("Lt", "Le") and b <= 0):
            declared.setdefault(a.name, {})[key] = True
        else:
            declared.setdefault(a.name, {})["real"] = True
    return declared


def run_sympy(workload, rounds):
    from sympy import And, ask
    from sympy.assumptions.lra_satask import lra_satask
    from sympy.core.cache import clear_cache
    from sympy.logic.algorithms.lra_theory import UnhandledInput

    plain = sympy_namespace(set(), {})
    results = {"answers": {}, "times": {}}
    methods = ["old assumptions", "ask", "lra_satask"]
    for m in methods:
        results["answers"][m] = [None] * len(workload["questions"])
        results["times"][m] = [[] for _ in workload["questions"]]
    results["times"]["construct"] = [[] for _ in workload["questions"]]
    for name, items in grouped(workload).items():
        raw = [eval(f, plain) for f in workload["facts"][name]]
        real_symbols = {s.name for head, a, b in raw if head in ORDER or head == "Eq" for s in (a - b).free_symbols}
        old_names = sympy_namespace(real_symbols, old_assumptions(raw))
        ask_names = sympy_namespace(real_symbols, {})
        ask_facts = And(*(sympy_predicate(eval(f, ask_names)) for f in workload["facts"][name]))
        for i, text in items:
            code = compile(text, "<q>", "eval")
            for _ in range(rounds):
                clear_cache()
                q, t = timed(lambda: eval(code, old_names))
                results["times"]["construct"][i].append(t)
                results["answers"]["old assumptions"][i], t = timed(lambda: sympy_old(q), LIMIT)
                results["times"]["old assumptions"][i].append(t)
                clear_cache()
                p = sympy_predicate(eval(code, ask_names))
                results["answers"]["ask"][i], t = timed(lambda: ask(p, ask_facts) is True, LIMIT)
                results["times"]["ask"][i].append(t)
                clear_cache()

                def lra():
                    try:
                        return lra_satask(p, ask_facts) is True
                    except (ValueError, TypeError, NotImplementedError, UnhandledInput):
                        return None

                results["answers"]["lra_satask"][i], t = timed(lra, LIMIT)
                results["times"]["lra_satask"][i].append(t)
            slow = {m: results["times"][m][i][-1] for m in methods if results["times"][m][i][-1] > 1e6}
            if slow:
                print(f"slow {name} {text} {slow}", file=sys.stderr)
    results["times"] = {k: [min(v) for v in values] for k, values in results["times"].items()}
    return results


def run_scaling(rounds):
    import nary.deciding as deciding
    from nary import Gt, Lt, Mul, NumberKind, exp

    rows = []
    for size in (1, 2, 4, 8, 16, 32, 64, 128):
        xs = [NumberKind(f"x{i}") for i in range(size + 1)]
        chain = [Lt(a, b) for a, b in zip(xs, xs[1:])]
        goals = [Lt(xs[0], xs[-1]), Lt(xs[-1], xs[0]), Gt(xs[size // 2] - xs[0], 0)]
        construct = min(timed(lambda: deciding.Facts(chain))[1] for _ in range(rounds))
        per_goal = []
        for g in goals:
            samples = []
            for _ in range(rounds):
                known = deciding.Facts(chain)
                samples.append(timed(lambda: known(g))[1])
            per_goal.append(min(samples))
        positive = [Gt(a, 0) for a in xs[:size]]
        product = Gt(Mul(*xs[:size]) + exp(xs[0]), 0) if size > 1 else Gt(xs[0] + exp(xs[0]), 0)
        samples = []
        for _ in range(rounds):
            known = deciding.Facts(positive)
            samples.append(timed(lambda: known(product))[1])
        rows.append({"size": size, "construct chain": construct, "chain goals": per_goal, "product": min(samples)})
    return rows


def run_sympy_scaling(rounds):
    from sympy import And, Mul, Q, Symbol, ask, exp
    from sympy.assumptions.lra_satask import lra_satask
    from sympy.core.cache import clear_cache

    rows = []
    for size in (1, 2, 4, 8, 16, 32, 64, 128):
        xs = [Symbol(f"x{i}", real=True) for i in range(size + 1)]
        chain = And(*(Q.lt(a, b) for a, b in zip(xs, xs[1:])))
        goals = [Q.lt(xs[0], xs[-1]), Q.lt(xs[-1], xs[0]), Q.positive(xs[size // 2] - xs[0])]
        per_goal = []
        for g in goals:
            samples = []
            for _ in range(rounds):
                clear_cache()
                samples.append(timed(lambda: lra_satask(g, chain))[1])
            per_goal.append(min(samples))
        positive = [Symbol(f"x{i}", positive=True) for i in range(size)]
        samples = []
        for _ in range(rounds):
            clear_cache()
            samples.append(timed(lambda: (Mul(*positive) + exp(positive[0])).is_positive)[1])
        ask_samples = []
        if size <= 16:
            facts = And(*(Q.positive(a) for a in xs[:size]))
            for _ in range(min(rounds, 3)):
                clear_cache()
                ask_samples.append(timed(lambda: ask(Q.positive(Mul(*xs[:size]) + exp(xs[0])), facts))[1])
        rows.append({
            "size": size, "chain goals": per_goal, "product, old assumptions": min(samples),
            "product, ask": min(ask_samples) if ask_samples else None,
        })
    return rows


def quantiles(values):
    ordered = sorted(values)
    return f"{statistics.median(ordered):,.1f} / {ordered[int(0.9 * (len(ordered) - 1))]:,.1f}"


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(map(str, row)) + " |" for row in rows])


def report(workload, nary, properties, sympy, scaling, sympy_scaling):
    categories = list(dict.fromkeys(q[0] for q in workload["questions"]))
    members = {c: [i for i, q in enumerate(workload["questions"]) if q[0] == c] for c in categories}
    members["all"] = list(range(len(workload["questions"])))
    engines = {"nary": nary["answers"], "properties.py": properties["answers"]}
    engines.update(sympy["answers"])
    print(table(["category", "questions", *engines], [
        [c, len(ix), *(sum(answers[i] is True for i in ix) for answers in engines.values())]
        for c, ix in members.items()
    ]))
    print()
    limits = {"nary": nary["times"]["first"], "properties.py": properties["times"]["one-shot"]}
    limits.update(sympy["times"])
    print(table(["engine", "proved, not by nary", "no answer", "out of time"], [
        [name, sum(a is True and not nary["answers"][i] for i, a in enumerate(answers)),
         sum(a is None for a in answers), sum(t >= LIMIT * 1e6 for t in limits[name])]
        for name, answers in engines.items()
    ]))
    print()
    times = {f"nary {k}": v for k, v in nary["times"].items()}
    times["properties.py one-shot"] = properties["times"]["one-shot"]
    times.update({f"sympy {k}": v for k, v in sympy["times"].items()})
    print(table(["median / p90 (us)", *members], [
        [name, *(quantiles([values[i] for i in ix]) for ix in members.values())] for name, values in times.items()
    ]))
    print()
    total, solver, translate = zip(*nary["split"])
    rest = [t - s - r for t, s, r in nary["split"]]
    print(table(["first question (us)", "median / p90", "share of the sum"], [
        [name, quantiles(values), f"{sum(values) / sum(total):.0%}"]
        for name, values in (("total", total), ("solver", solver), ("translation", translate), ("chaining", rest))
    ]))
    print()
    print(table(["facts", "setup (us)"], [[name, f"{t:,.1f}"] for name, t in nary["setup"].items()]))
    print()
    print(table(["n", "nary facts", "nary goals", "lra_satask goals", "nary product", "old product", "ask product"], [
        [row["size"], f"{row['construct chain']:,.0f}", " ".join(f"{t:,.0f}" for t in row["chain goals"]),
         " ".join(f"{t:,.0f}" for t in other["chain goals"]), f"{row['product']:,.0f}",
         f"{other['product, old assumptions']:,.0f}",
         "" if other["product, ask"] is None else f"{other['product, ask']:,.0f}"]
        for row, other in zip(scaling, sympy_scaling)
    ]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["workload", "nary", "properties", "sympy", "scaling", "sympy-scaling", "report"])
    parser.add_argument("--workload", default="workload.json")
    parser.add_argument("--output")
    parser.add_argument("--cap", type=int, default=400)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--results", nargs=5)
    args = parser.parse_args()
    if args.command == "workload":
        write_workload(args.workload, args.cap)
        return
    if args.command == "report":
        loaded = [json.loads(Path(path).read_text()) for path in args.results]
        report(json.loads(Path(args.workload).read_text()), *loaded)
        return
    sys.setrecursionlimit(10000)
    resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    workload = json.loads(Path(args.workload).read_text()) if args.command in ("nary", "properties", "sympy") else None
    run = {
        "nary": lambda: run_nary(workload, args.rounds),
        "properties": lambda: run_properties(workload, args.rounds),
        "sympy": lambda: run_sympy(workload, args.rounds),
        "scaling": lambda: run_scaling(args.rounds),
        "sympy-scaling": lambda: run_sympy_scaling(args.rounds),
    }[args.command]
    Path(args.output).write_text(json.dumps(run()))


if __name__ == "__main__":
    main()
