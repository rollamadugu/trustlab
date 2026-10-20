"""The unified trustworthiness metric.

Core idea of the thesis: a GREEN verdict from any AI-testing modality can be
assigned a *trust score* in [0,1] -- the estimated probability that the green is
sound -- computed only from OBSERVABLE features (never ground truth). The score
is produced by a small, interpretable logistic model trained on labelled
verdicts (trustworthy vs. false pass). The same framework is instantiated per
modality with a modality-specific feature view, which is how one metric
generalises across oracle / heal / adjudicate.

Two definitions used throughout:

  * False-Confidence Gap (FCG) = among green verdicts, the fraction that are
    actually false passes. It is exactly the error of the NAIVE policy
    "trust every green", and the phenomenon the thesis measures.

  * A trustworthy green verdict has label y=1 (ground_truth_ok); a false pass
    has y=0. The trust metric must rank y=1 above y=0 (high ROC-AUC) and be
    calibrated (low ECE).

Pure standard library: the logistic model is trained with gradient descent.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from ..verdict import Verdict

# The observable features each modality exposes to the trust metric. Order
# matters (defines the model's input vector). None of these is ground truth.
FEATURE_KEYS: Dict[str, List[str]] = {
    "oracle": ["mean_strength", "frac_exact", "output_diversity",
               "input_diversity", "min_strength", "n_tests", "coverage",
               "exact_coverage", "strength_x_cov", "exact_x_cov"],
    "heal": ["match_confidence", "ambiguity", "attrs_agreed", "n_candidates",
             "change_intensity_proxy"],
    "judge": ["consistency", "evidence", "self_confidence", "n_samples"],
}


def featurize(v: Verdict) -> List[float]:
    keys = FEATURE_KEYS[v.modality]
    return [float(v.features.get(k, 0.0)) for k in keys]


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


@dataclass
class TrustModel:
    """Standardising logistic-regression trust model (trained via GD)."""

    modality: str
    weights: List[float] = field(default_factory=list)
    bias: float = 0.0
    mu: List[float] = field(default_factory=list)
    sd: List[float] = field(default_factory=list)

    # ---- training ----
    def fit(self, X: List[List[float]], y: List[int], lr: float = 0.3,
            epochs: int = 400, l2: float = 1e-3, seed: int = 0) -> "TrustModel":
        n = len(X)
        d = len(X[0]) if n else 0
        # standardise features for stable optimisation
        self.mu = [sum(row[j] for row in X) / n for j in range(d)]
        self.sd = []
        for j in range(d):
            var = sum((row[j] - self.mu[j]) ** 2 for row in X) / n
            self.sd.append(math.sqrt(var) or 1.0)
        Xs = [[(row[j] - self.mu[j]) / self.sd[j] for j in range(d)] for row in X]

        rng = random.Random(seed)
        self.weights = [rng.uniform(-0.01, 0.01) for _ in range(d)]
        self.bias = 0.0
        for _ in range(epochs):
            gw = [0.0] * d
            gb = 0.0
            for row, yi in zip(Xs, y):
                z = self.bias + sum(w * x for w, x in zip(self.weights, row))
                p = _sigmoid(z)
                err = p - yi
                for j in range(d):
                    gw[j] += err * row[j]
                gb += err
            for j in range(d):
                self.weights[j] -= lr * (gw[j] / n + l2 * self.weights[j])
            self.bias -= lr * (gb / n)
        return self

    def predict_proba(self, x: List[float]) -> float:
        xs = [(x[j] - self.mu[j]) / self.sd[j] for j in range(len(x))]
        z = self.bias + sum(w * v for w, v in zip(self.weights, xs))
        return _sigmoid(z)

    def score_verdict(self, v: Verdict) -> float:
        return self.predict_proba(featurize(v))


def train_trust_model(green_verdicts: Sequence[Verdict], modality: str,
                      seed: int = 0, **fit_kw) -> TrustModel:
    """Train a trust model on GREEN verdicts (label = ground_truth_ok)."""
    X = [featurize(v) for v in green_verdicts]
    y = [1 if v.ground_truth_ok else 0 for v in green_verdicts]
    return TrustModel(modality=modality).fit(X, y, seed=seed, **fit_kw)


def false_confidence_gap(verdicts: Sequence[Verdict]) -> float:
    """Among GREEN verdicts, the fraction that are false passes = error of the
    'trust every green' policy."""
    green = [v for v in verdicts if v.apparent_ok]
    if not green:
        return 0.0
    return sum(1 for v in green if v.false_pass) / len(green)


def naive_trust(v: Verdict) -> float:
    """Baseline policy: a green verdict is fully trusted (1.0), else 0.0."""
    return 1.0 if v.apparent_ok else 0.0
