"""Modality 3 -- AI-adjudicated verdicts (LLM-as-judge / flake adjudication).

An AI judge decides whether a test outcome is really OK (or whether a red build
is a real bug vs. flaky noise). Judges *hallucinate*: they sometimes declare OK
when the run actually failed -- a false pass -- and their *self-reported
confidence is over-confident* (poorly calibrated), which is the documented
failure mode.

Ground truth is the hidden true state of the run. Observable signals the trust
metric may use: evidence strength, and **self-consistency** across repeated
independent judgements (a cheap, powerful signal the raw confidence ignores).
"""
from __future__ import annotations

import math
import random
from typing import List

from ..verdict import Verdict


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def _one_case(rng: random.Random, n_samples: int = 5) -> Verdict:
    truth_ok = rng.random() < 0.5                 # hidden: is the run actually OK?
    difficulty = rng.uniform(0.0, 1.0)            # hidden hardness of the case
    evidence = max(0.0, min(1.0, rng.gauss(1.0 - difficulty, 0.15)))  # observable (noisy)

    # probability the judge is correct on a single sample
    p_correct = _sigmoid(3.2 * evidence - 2.6 * difficulty + 0.2)

    samples = []
    for _ in range(n_samples):
        correct = rng.random() < p_correct
        verdict_ok = truth_ok if correct else (not truth_ok)
        samples.append(verdict_ok)

    # the "headline" judgement = majority vote of the samples
    ok_votes = sum(1 for v in samples if v)
    apparent_ok = ok_votes >= (n_samples / 2.0)
    # self-consistency: agreement among samples (observable)
    consistency = max(ok_votes, n_samples - ok_votes) / n_samples
    # over-confident self-report (observable but miscalibrated)
    self_conf = min(0.99, 0.6 + 0.4 * evidence)

    features = {
        "self_confidence": self_conf,
        "evidence": evidence,
        "consistency": consistency,
        "n_samples": float(n_samples),
    }
    return Verdict(modality="judge", subject="run",
                   apparent_ok=apparent_ok, ground_truth_ok=truth_ok,
                   features=features,
                   info={"difficulty": round(difficulty, 3)})


def generate_adjudication_verdicts(rng: random.Random, n: int = 400,
                                   n_samples: int = 5) -> List[Verdict]:
    return [_one_case(rng, n_samples) for _ in range(n)]
