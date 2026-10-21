"""Experiment 3 -- escape rate by mutation-operator class (actionable breakdown).

Instead of one combined fault-detection number, this breaks the oracle result
down by *fault type*. For each mutation operator class we report the **escape
rate**: the fraction of injected faults of that class that AI-generated suites
fail to catch (go green on anyway). This answers "which kinds of bug do weak AI
oracles miss most?" -- a far more actionable finding than a single percentage.

Operators: AOR (arithmetic), ROR (relational / off-by-one), LCR (logical
connector), CRP (constant), UOD (unary 'not' deletion).

Escape rate is computed per seed, then averaged with a 95% bootstrap CI across
seeds. The pooled proportion also gets a Wilson interval. Grounded in real
mutation testing.

Writes results/exp3_escape_by_operator.json.
"""
from __future__ import annotations

import json
import os
import random
from collections import defaultdict
from typing import Dict, List

from trustlab.metrics.stats import bootstrap_ci, summarize, wilson_interval
from trustlab.modalities.oracles import escape_counts_by_operator

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")

OP_LABEL = {
    "AOR": "Arithmetic (+ - * /)",
    "ROR": "Relational (< > == off-by-one)",
    "LCR": "Logical (and / or)",
    "CRP": "Constant",
    "UOD": "Unary 'not' deletion",
}


def run(seeds: int = 15, suites_per_subject: int = 60) -> Dict:
    per_seed_rate: Dict[str, List[float]] = defaultdict(list)
    pooled: Dict[str, Dict[str, int]] = defaultdict(lambda: {"killed": 0, "total": 0})

    for s in range(seeds):
        rng = random.Random(s + 1)
        counts = escape_counts_by_operator(rng, suites_per_subject=suites_per_subject)
        for op, c in counts.items():
            if c["total"] == 0:
                continue
            escape = 1.0 - c["killed"] / c["total"]
            per_seed_rate[op].append(escape)
            pooled[op]["killed"] += c["killed"]
            pooled[op]["total"] += c["total"]

    operators = {}
    for op in sorted(per_seed_rate, key=lambda o: -summarize(per_seed_rate[o])["mean"]):
        rates = per_seed_rate[op]
        lo, hi = bootstrap_ci(rates, seed=11)
        k_escaped = pooled[op]["total"] - pooled[op]["killed"]
        w_lo, w_hi = wilson_interval(k_escaped, pooled[op]["total"])
        operators[op] = {
            "label": OP_LABEL.get(op, op),
            "escape_rate_mean": round(summarize(rates)["mean"], 4),
            "escape_rate_ci95_across_seeds": [round(lo, 4), round(hi, 4)],
            "pooled_escape_rate": round(k_escaped / pooled[op]["total"], 4),
            "pooled_wilson_ci95": [round(w_lo, 4), round(w_hi, 4)],
            "mutant_trials": pooled[op]["total"],
        }

    return {
        "experiment": "escape_rate_by_operator",
        "seeds": seeds,
        "suites_per_subject": suites_per_subject,
        "note": "escape rate = fraction of injected faults of this class that "
                "AI-generated suites FAILED to catch (lower is better).",
        "operators": operators,
    }


def main() -> None:
    out = run()
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.abspath(os.path.join(RESULTS, "exp3_escape_by_operator.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print("Experiment 3 -- escape rate by mutation-operator class")
    print(f"  seeds = {out['seeds']}, suites/subject = {out['suites_per_subject']}")
    print(f"  (escape rate = faults of this class AI suites did NOT catch; lower is better)\n")
    for op, d in out["operators"].items():
        lo, hi = d["escape_rate_ci95_across_seeds"]
        print(f"  {op:4s} {d['label']:34s} escape {d['escape_rate_mean']:.1%} "
              f"95% CI [{lo:.1%}, {hi:.1%}]   (n={d['mutant_trials']})")
    print(f"\n  wrote {path}")


if __name__ == "__main__":
    main()
