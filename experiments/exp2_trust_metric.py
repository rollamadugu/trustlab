"""Experiment 2 -- does the trust metric let us believe the right greens?

Hypotheses:
  H1  The trust metric ranks trustworthy greens above false passes far better
      than the naive "trust the green" policy (ROC-AUC >> 0.5).
  H2  The trust score is calibrated (low ECE), so it can be used as a probability.
  H3  Operationally, accepting only high-trust greens sharply cuts the false-pass
      rate among accepted verdicts versus naive, at a reasonable retention.

Evaluated per modality over many seeds (train/test split each seed), with
Mann-Whitney U + Vargha-Delaney A12 on trust(trustworthy) vs trust(false pass),
mean ROC-AUC, mean ECE, and the operational false-pass reduction at 70% retention.

Writes results/exp2_trust_metric.json.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

from trustlab.benchmark import build_modality, generate_all
from trustlab.metrics.stats import (a12_magnitude, expected_calibration_error,
                                     mann_whitney_u, roc_auc, summarize,
                                     vargha_delaney_a12)

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")


def _operational(scores: List[float], labels: List[int],
                 retain: float = 0.7) -> Tuple[float, float, float]:
    """Accept the top-`retain` fraction of greens by trust. Returns
    (accepted_false_pass_rate, actual_retention, naive_false_pass_rate)."""
    n = len(scores)
    if n == 0:
        return 0.0, 0.0, 0.0
    naive_fp = sum(1 for y in labels if y == 0) / n
    order = sorted(range(n), key=lambda i: scores[i], reverse=True)
    k = max(1, int(round(n * retain)))
    accepted = order[:k]
    acc_fp = sum(1 for i in accepted if labels[i] == 0) / k
    return acc_fp, k / n, naive_fp


def run(seeds: int = 15, retain: float = 0.7) -> Dict:
    agg: Dict[str, Dict[str, List[float]]] = {
        m: {"auc": [], "ece": [], "a12": [], "p": [], "acc_fp": [], "naive_fp": []}
        for m in ("oracle", "heal", "judge")
    }
    for s in range(seeds):
        data = generate_all(s)
        for modality, verdicts in data.items():
            res = build_modality(modality, verdicts, seed=s)
            test = [res.green[i] for i in res.test_idx]
            scores = [v.trust for v in test]
            labels = [1 if v.ground_truth_ok else 0 for v in test]
            trustworthy = [sc for sc, y in zip(scores, labels) if y == 1]
            falsepass = [sc for sc, y in zip(scores, labels) if y == 0]
            a12 = vargha_delaney_a12(trustworthy, falsepass)
            _, p = mann_whitney_u(trustworthy, falsepass)
            acc_fp, _, naive_fp = _operational(scores, labels, retain)
            agg[modality]["auc"].append(res.trust_auc)
            agg[modality]["ece"].append(res.ece)
            agg[modality]["a12"].append(a12)
            agg[modality]["p"].append(p)
            agg[modality]["acc_fp"].append(acc_fp)
            agg[modality]["naive_fp"].append(naive_fp)

    out = {"experiment": "trust_metric", "seeds": seeds, "retention_target": retain,
           "modalities": {}}
    for m, d in agg.items():
        auc = summarize(d["auc"])
        out["modalities"][m] = {
            "trust_roc_auc": {"mean": round(auc["mean"], 4), "std": round(auc["std"], 4)},
            "naive_roc_auc": 0.5,
            "ece": round(summarize(d["ece"])["mean"], 4),
            "a12_trustworthy_vs_falsepass": round(summarize(d["a12"])["mean"], 4),
            "a12_magnitude": a12_magnitude(summarize(d["a12"])["mean"]),
            "mann_whitney_p_median": round(sorted(d["p"])[len(d["p"]) // 2], 6),
            "false_pass_rate_naive": round(summarize(d["naive_fp"])["mean"], 4),
            "false_pass_rate_trust_at_retain": round(summarize(d["acc_fp"])["mean"], 4),
        }
    return out


def main() -> None:
    out = run()
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.abspath(os.path.join(RESULTS, "exp2_trust_metric.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print("Experiment 2 -- trust metric vs naive 'trust the green'")
    print(f"  seeds = {out['seeds']}, operating point = accept top {int(out['retention_target']*100)}% by trust")
    for m, d in out["modalities"].items():
        print(f"\n  [{m}]")
        print(f"    trust ROC-AUC  = {d['trust_roc_auc']['mean']:.3f} "
              f"(std {d['trust_roc_auc']['std']:.3f})   vs naive 0.500")
        print(f"    effect size A12(trustworthy>falsepass) = {d['a12_trustworthy_vs_falsepass']:.3f} "
              f"({d['a12_magnitude']}), Mann-Whitney p = {d['mann_whitney_p_median']}")
        print(f"    calibration ECE = {d['ece']:.3f}")
        print(f"    false-pass rate among accepted:  naive={d['false_pass_rate_naive']:.1%}  "
              f"-> trust={d['false_pass_rate_trust_at_retain']:.1%}")
    print(f"\n  wrote {path}")


if __name__ == "__main__":
    main()
