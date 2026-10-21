"""Modality 1 -- AI-generated test oracles.

This is the most rigorous modality: a verdict's *soundness* is decided by real
mutation testing, not a model. We model only one thing about the AI -- the
*strength distribution of the assertions it writes* -- because that is precisely
what the empirical literature found LLM oracles get wrong: they tend to produce
weak / behaviour-echoing assertions (type checks, "no exception", loose ranges)
that look like tests but catch few real bugs.

A verdict = running one AI-generated suite against one program-under-test (PUT):
  * PUT is either the CORRECT program or a MUTANT (an injected bug).
  * apparent_ok     = the suite is GREEN on the PUT.
  * ground_truth_ok = the PUT is actually the correct program.
  * false_pass      = green on a mutant (the suite failed to catch a real bug).

The trust metric is later given only the suite's observable `features`
(assertion strength, input diversity, breadth) -- never the ground truth -- and
must predict which green verdicts are false passes.
"""
from __future__ import annotations

import ast
import random
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Tuple

from ..sut.mutation import Mutant, generate_mutants
from ..sut.programs import SUBJECTS, Subject
from ..verdict import Verdict


def _executable_lines(source: str) -> set:
    """Line numbers of executable statements (excludes the def header)."""
    tree = ast.parse(source)
    lines = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and not isinstance(node, ast.FunctionDef):
            lines.add(node.lineno)
    return lines


def _line_coverage(subject: Subject, ref: Callable, arg_list: List[tuple]) -> float:
    """Real statement coverage of `ref` by the suite inputs (observable signal,
    exactly what a QA coverage tool reports)."""
    total = _executable_lines(subject.source)
    if not total:
        return 1.0
    executed = set()

    def tracer(frame, event, arg):
        if event == "line" and frame.f_code.co_name == subject.func_name:
            executed.add(frame.f_lineno)
        return tracer

    old = sys.gettrace()
    sys.settrace(tracer)
    try:
        for a in arg_list:
            try:
                ref(*a)
            except Exception:
                pass
    finally:
        sys.settrace(old)
    return len(executed & total) / len(total)


class OracleKind(str, Enum):
    EXACT = "exact"     # assert out == expected                 (strong)
    RANGE = "range"     # assert lo <= out <= hi (numeric)       (medium)
    MEMBER = "member"   # assert out in {all seen labels}        (weak)
    TYPE = "type"       # assert type(out) == expected type      (very weak)
    NOEXC = "noexc"     # assert the call did not raise          (weakest)


# nominal assertion strength in [0,1] (an observable prior, not ground truth)
STRENGTH = {
    OracleKind.EXACT: 1.0,
    OracleKind.RANGE: 0.55,
    OracleKind.MEMBER: 0.30,
    OracleKind.TYPE: 0.15,
    OracleKind.NOEXC: 0.05,
}

# Default assertion-strength distribution of an "AI" oracle generator. Skewed
# toward weak assertions to reflect the documented behaviour; override to study
# stronger/weaker generators.
AI_DIST_DEFAULT = {
    OracleKind.EXACT: 0.35,
    OracleKind.RANGE: 0.20,
    OracleKind.MEMBER: 0.20,
    OracleKind.TYPE: 0.15,
    OracleKind.NOEXC: 0.10,
}


@dataclass
class _Test:
    args: tuple
    kind: OracleKind
    expected: object
    band: Tuple[float, float] = (0.0, 0.0)
    labels: Tuple = ()
    exp_type: type = object


@dataclass
class AISuite:
    subject: str
    tests: List[_Test]
    coverage: float = 0.0            # statement coverage of the SUT (observable)
    exact_coverage: float = 0.0      # coverage by EXACT-assertion tests only

    def check_one(self, t: _Test, func: Callable) -> bool:
        """True == this test PASSES (does not flag a problem) for func."""
        try:
            out = func(*t.args)
        except Exception:
            return t.kind == OracleKind.NOEXC and False  # exception always fails NOEXC too
        if t.kind == OracleKind.EXACT:
            return out == t.expected
        if t.kind == OracleKind.RANGE:
            try:
                return t.band[0] <= out <= t.band[1]
            except TypeError:
                return out == t.expected
        if t.kind == OracleKind.MEMBER:
            return out in t.labels
        if t.kind == OracleKind.TYPE:
            return type(out) is t.exp_type
        if t.kind == OracleKind.NOEXC:
            return True  # reached here => no exception
        return True

    def green_on(self, func: Callable) -> bool:
        """Suite is GREEN iff every test passes."""
        return all(self.check_one(t, func) for t in self.tests)

    # ---- observable features (no ground truth) --------------------------------
    def features(self) -> Dict[str, float]:
        n = len(self.tests)
        strengths = [STRENGTH[t.kind] for t in self.tests]
        frac_exact = sum(1 for t in self.tests if t.kind == OracleKind.EXACT) / n
        distinct_expected = len({repr(t.expected) for t in self.tests})
        distinct_args = len({repr(t.args) for t in self.tests})
        mean_strength = sum(strengths) / n
        out_div = distinct_expected / n
        in_div = distinct_args / n
        cov = self.coverage
        return {
            "n_tests": float(n),
            "mean_strength": mean_strength,
            "min_strength": min(strengths),
            "frac_exact": frac_exact,
            "output_diversity": out_div,
            "input_diversity": in_div,
            "coverage": cov,
            # the key signal: coverage achieved specifically by STRONG (exact)
            # assertions. A mutant is only caught when an exact assertion's input
            # exercises the buggy branch, so this tracks true fault-detection.
            "exact_coverage": self.exact_coverage,
            "strength_x_cov": mean_strength * cov,
            "exact_x_cov": frac_exact * cov,
        }


def _make_suite(subject: Subject, ref: Callable, rng: random.Random,
                dist: Dict[OracleKind, float], n_tests: int) -> AISuite:
    inputs = list(subject.inputs)
    rng.shuffle(inputs)
    chosen = inputs[: min(n_tests, len(inputs))]
    # global label set / value range for weak oracles, derived from correct behaviour
    all_outs = [ref(*a) for a in subject.inputs]
    labels = tuple(sorted({o for o in all_outs}, key=repr))
    numeric = all(isinstance(o, (int, float)) and not isinstance(o, bool) for o in all_outs)
    gmin = min(all_outs) if numeric else 0
    gmax = max(all_outs) if numeric else 0

    kinds = list(dist.keys())
    weights = list(dist.values())
    tests: List[_Test] = []
    for args in chosen:
        expected = ref(*args)
        kind = rng.choices(kinds, weights=weights, k=1)[0]
        # categorical / boolean outputs cannot use RANGE -> fall back to MEMBER
        # (bool is a subtype of int, so exclude it explicitly)
        is_num = isinstance(expected, (int, float)) and not isinstance(expected, bool)
        if kind == OracleKind.RANGE and not is_num:
            kind = OracleKind.MEMBER
        band = (0.0, 0.0)
        if kind == OracleKind.RANGE and numeric:
            lo = min(gmin, expected) - abs(expected) * 0.5 - 1
            hi = max(gmax, expected) + abs(expected) * 0.5 + 1
            band = (lo, hi)
        tests.append(_Test(args=args, kind=kind, expected=expected, band=band,
                           labels=labels, exp_type=type(expected)))
    cov = _line_coverage(subject, ref, [t.args for t in tests])
    exact_args = [t.args for t in tests if t.kind == OracleKind.EXACT]
    exact_cov = _line_coverage(subject, ref, exact_args) if exact_args else 0.0
    return AISuite(subject.name, tests, coverage=cov, exact_coverage=exact_cov)


def suite_mutation_score(suite: AISuite, ref, mutants) -> float:
    """Real fault-detection power: fraction of non-equivalent mutants the suite
    catches (goes non-green on). Ground truth via mutation testing."""
    pool = [m for m in mutants if m.func is not None and not m.equivalent]
    if not pool:
        return 0.0
    killed = sum(1 for m in pool if not suite.green_on(m.func))
    return killed / len(pool)


def escape_counts_by_operator(rng: random.Random, suites_per_subject: int = 60,
                              n_tests: int = 10,
                              dist: Dict[OracleKind, float] = None) -> Dict[str, Dict[str, int]]:
    """For each mutation operator class (AOR/ROR/LCR/CRP/UOD), count how often a
    mutant of that class is *killed* vs *escapes* across AI-generated suites.

    This breaks the single combined fault-detection number down by fault *type*,
    which is far more actionable: it shows which kinds of bugs AI oracles miss
    most (e.g. off-by-one / relational faults vs. logical-connector faults).
    Returns ``{operator: {"killed": k, "total": t}}``.
    """
    dist = dist or AI_DIST_DEFAULT
    counts: Dict[str, Dict[str, int]] = {}
    for subject in SUBJECTS:
        ref = subject.compile_ref()
        mutants = [m for m in generate_mutants(subject)
                   if m.func is not None and not m.equivalent]
        if not mutants:
            continue
        suites = [_make_suite(subject, ref, rng, dist, n_tests)
                  for _ in range(suites_per_subject)]
        for m in mutants:
            bucket = counts.setdefault(m.operator, {"killed": 0, "total": 0})
            for suite in suites:
                bucket["total"] += 1
                if not suite.green_on(m.func):   # suite goes red => fault caught
                    bucket["killed"] += 1
    return counts


def generate_oracle_verdicts(rng: random.Random, suites_per_subject: int = 80,
                             n_tests: int = 10,
                             dist: Dict[OracleKind, float] = None,
                             tau: float = 0.8) -> List[Verdict]:
    """Produce one verdict per AI-generated suite.

    The suite is run against the (correct) program and is GREEN. The real
    question -- can you *believe* that green? -- is answered by the suite's true
    fault-detection power (mutation score): a green suite is SOUND iff it would
    actually catch bugs (mutation score >= tau). A green-but-unsound suite is a
    *false pass*: it makes the code look tested when it is not.

      apparent_ok     = suite is green on the correct program (True by design)
      ground_truth_ok = suite is sound (mutation score >= tau)
      features        = observable suite signals (assertion strength, diversity)
    """
    dist = dist or AI_DIST_DEFAULT
    verdicts: List[Verdict] = []
    for subject in SUBJECTS:
        ref = subject.compile_ref()
        mutants = [m for m in generate_mutants(subject)
                   if m.func is not None and not m.equivalent]
        if not mutants:
            continue
        for _ in range(suites_per_subject):
            suite = _make_suite(subject, ref, rng, dist, n_tests)
            ms = suite_mutation_score(suite, ref, mutants)
            green = suite.green_on(ref)
            verdicts.append(Verdict(
                modality="oracle", subject=subject.name,
                apparent_ok=green, ground_truth_ok=(ms >= tau),
                features=suite.features(),
                info={"mutation_score": round(ms, 4), "tau": tau}))
    return verdicts
