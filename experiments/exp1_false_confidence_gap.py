"""Experiment 1 -- the headline phenomenon: the False-Confidence Gap (FCG).

Research question: across AI-testing modalities, what fraction of GREEN verdicts
(results that claim "OK") are actually *false passes* -- sound-looking but unable
to catch a real bug / healed onto the wrong element / hallucinated?

FCG is exactly the error rate of today's default policy: "trust the green".
We measure it over many seeds for stability and report per-modality means with
spread, plus the oracle breakdown per subject (grounded in real mutation score).

Writes results/exp1_false_confidence_gap.json.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List

from trustlab.benchmark import generate_all
from trustlab.metrics.stats import bootstrap_ci, summarize
from trustlab.trust.metric import false_confidence_gap

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")


def run(seeds: int = 15) -> Dict:
    per_modality: Dict[str, List[float]] = {"oracle": [], "heal": [], "judge": []}
    green_counts: Dict[str, List[float]] = {"oracle": [], "heal": [], "judge": []}
    oracle_by_subject: Dict[str, List[float]] = {}

    for s in range(seeds):
        data = generate_all(s)
        for modality, verdicts in data.items():
            green = [v for v in verdicts if v.apparent_ok]
            per_modality[modality].append(false_confidence_gap(verdicts))
            green_counts[modality].append(len(green))
            if modality == "oracle":
                subs = {v.subject for v in verdicts}
                for sub in subs:
                    vv = [v for v in verdicts if v.subject == sub and v.apparent_ok]
                    if vv:
                        fp = sum(1 for v in vv if v.false_pass) / len(vv)
                        oracle_by_subject.setdefault(sub, []).append(fp)

    out = {
        "experiment": "false_confidence_gap",
        "seeds": seeds,
        "modalities": {
            m: {"false_confidence_gap": summarize(per_modality[m]),
                "ci95": [round(c, 4) for c in bootstrap_ci(per_modality[m], seed=7)],
                "mean_green_per_run": summarize(green_counts[m])["mean"]}
            for m in per_modality
        },
        "oracle_fcg_by_subject": {
            sub: round(summarize(v)["mean"], 4) for sub, v in sorted(oracle_by_subject.items())
        },
    }
    return out


def main() -> None:
    out = run()
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.abspath(os.path.join(RESULTS, "exp1_false_confidence_gap.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print("Experiment 1 -- False-Confidence Gap (fraction of GREEN verdicts that are false passes)")
    print(f"  seeds = {out['seeds']}")
    for m, d in out["modalities"].items():
        g = d["false_confidence_gap"]
        lo, hi = d["ci95"]
        print(f"  {m:7s}  FCG = {g['mean']:.1%}  95% CI [{lo:.1%}, {hi:.1%}]  "
              f"(std {g['std']:.1%})   ~{d['mean_green_per_run']:.0f} green/run")
    print("\n  interpretation: 'trust the green' is wrong this often. "
          "A large FCG == large hidden false confidence.")
    print("  oracle FCG by subject (real mutation-score ground truth):")
    for sub, fcg in out["oracle_fcg_by_subject"].items():
        print(f"     {sub:14s} {fcg:.1%}")
    print(f"  wrote {path}")


if __name__ == "__main__":
    main()
