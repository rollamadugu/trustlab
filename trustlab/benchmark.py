"""Benchmark builder: a labelled verdict corpus across all three modalities.

This is a released research artefact: a dataset of AI-testing verdicts, each
labelled with ground-truth soundness (trustworthy vs. false pass), the
observable features, and the trust metric's score. It is also the shared harness
the experiments reuse so results are consistent.

Protocol (per modality, fully seeded -> reproducible):
  1. generate verdicts,
  2. keep GREEN verdicts (the ones that claim OK -- the population at risk),
  3. split train/test, train the trust model on train,
  4. score every green verdict with the trust model,
  5. record False-Confidence Gap, trust ROC-AUC (test), and ECE (test).
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .modalities import (generate_adjudication_verdicts, generate_healing_verdicts,
                         generate_oracle_verdicts)
from .metrics.stats import expected_calibration_error, roc_auc
from .trust.metric import TrustModel, false_confidence_gap, train_trust_model
from .verdict import Verdict


def generate_all(seed: int, oracle_suites: int = 80, heal_n: int = 1200,
                 judge_n: int = 1200) -> Dict[str, List[Verdict]]:
    return {
        "oracle": generate_oracle_verdicts(random.Random(seed + 1),
                                           suites_per_subject=oracle_suites),
        "heal": generate_healing_verdicts(random.Random(seed + 2), n=heal_n),
        "judge": generate_adjudication_verdicts(random.Random(seed + 3), n=judge_n),
    }


@dataclass
class ModalityResult:
    modality: str
    n_total: int
    n_green: int
    false_confidence_gap: float
    trust_auc: float
    ece: float
    model: TrustModel
    green: List[Verdict] = field(default_factory=list)
    test_idx: List[int] = field(default_factory=list)


def build_modality(modality: str, verdicts: List[Verdict], seed: int,
                   train_frac: float = 0.6) -> ModalityResult:
    green = [v for v in verdicts if v.apparent_ok]
    rng = random.Random(seed)
    order = list(range(len(green)))
    rng.shuffle(order)
    k = int(len(order) * train_frac)
    train_idx, test_idx = order[:k], order[k:]
    train = [green[i] for i in train_idx]

    model = train_trust_model(train, modality, seed=seed)
    for v in green:
        v.trust = model.score_verdict(v)

    test = [green[i] for i in test_idx]
    scores = [v.trust for v in test]
    labels = [1 if v.ground_truth_ok else 0 for v in test]
    return ModalityResult(
        modality=modality,
        n_total=len(verdicts),
        n_green=len(green),
        false_confidence_gap=false_confidence_gap(verdicts),
        trust_auc=roc_auc(scores, labels),
        ece=expected_calibration_error(scores, labels, bins=8),
        model=model,
        green=green,
        test_idx=test_idx,
    )


def build_benchmark(seed: int = 0) -> Tuple[Dict[str, ModalityResult], Dict]:
    data = generate_all(seed)
    results: Dict[str, ModalityResult] = {}
    records: List[Dict] = []
    for modality, verdicts in data.items():
        res = build_modality(modality, verdicts, seed)
        results[modality] = res
        test_set = set(res.test_idx)
        for i, v in enumerate(res.green):
            rec = v.as_dict()
            rec["split"] = "test" if i in test_set else "train"
            records.append(rec)
    summary = {
        "seed": seed,
        "modalities": {
            m: {"n_total": r.n_total, "n_green": r.n_green,
                "false_confidence_gap": round(r.false_confidence_gap, 4),
                "trust_auc": round(r.trust_auc, 4), "ece": round(r.ece, 4)}
            for m, r in results.items()
        },
    }
    return results, {"summary": summary, "verdicts": records}


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(os.path.join(here, "..", "results"))
    os.makedirs(out_dir, exist_ok=True)
    _, payload = build_benchmark(seed=0)
    path = os.path.join(out_dir, "trust_benchmark.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print("Benchmark written:", path)
    for m, s in payload["summary"]["modalities"].items():
        print(f"  {m:7s} green={s['n_green']:5d}  FCG={s['false_confidence_gap']:.1%}  "
              f"trust_AUC={s['trust_auc']:.3f}  ECE={s['ece']:.3f}")


if __name__ == "__main__":
    main()
