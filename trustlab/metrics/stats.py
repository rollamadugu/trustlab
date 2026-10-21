"""Statistics (pure standard library): ranking quality, significance, effect
size, and calibration -- the rigour a committee expects."""
from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple


def _avg_ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i, n = 0, len(values)
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    return ranks


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def mann_whitney_u(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float]:
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0.0, 1.0
    allv = list(a) + list(b)
    ranks = _avg_ranks(allv)
    r_a = sum(ranks[:m])
    u_a = r_a - m * (m + 1) / 2.0
    mu = m * n / 2.0
    N = m + n
    counts: Dict[float, int] = {}
    for v in allv:
        counts[v] = counts.get(v, 0) + 1
    tie = sum(t ** 3 - t for t in counts.values())
    var = (m * n / 12.0) * ((N + 1) - tie / (N * (N - 1))) if N > 1 else 0.0
    if var <= 0:
        return u_a, 1.0
    z = (u_a - mu) / math.sqrt(var)
    return u_a, max(0.0, min(1.0, 2.0 * (1.0 - _phi(abs(z)))))


def vargha_delaney_a12(a: Sequence[float], b: Sequence[float]) -> float:
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0.5
    gt = eq = 0
    for x in a:
        for y in b:
            if x > y:
                gt += 1
            elif x == y:
                eq += 1
    return (gt + 0.5 * eq) / (m * n)


def a12_magnitude(a12: float) -> str:
    d = abs(a12 - 0.5)
    if d < 0.06:
        return "negligible"
    if d < 0.14:
        return "small"
    if d < 0.21:
        return "medium"
    return "large"


def roc_auc(scores: Sequence[float], labels: Sequence[int]) -> float:
    """AUC = P(score of a positive > score of a negative), ties = 0.5.
    labels: 1 == positive (trustworthy), 0 == negative (false pass)."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return float("nan")
    gt = eq = 0
    for p in pos:
        for q in neg:
            if p > q:
                gt += 1
            elif p == q:
                eq += 1
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def reliability_bins(scores: Sequence[float], correct: Sequence[int],
                     bins: int = 10) -> List[Dict[str, float]]:
    edges = [i / bins for i in range(bins + 1)]
    out = []
    n = len(scores)
    for b in range(bins):
        lo, hi = edges[b], edges[b + 1]
        idx = [i for i in range(n)
               if (scores[i] > lo or (b == 0 and scores[i] >= lo)) and scores[i] <= hi]
        if not idx:
            continue
        conf = sum(scores[i] for i in idx) / len(idx)
        acc = sum(correct[i] for i in idx) / len(idx)
        out.append({"lo": lo, "hi": hi, "n": len(idx), "confidence": conf, "accuracy": acc})
    return out


def expected_calibration_error(scores: Sequence[float], correct: Sequence[int],
                               bins: int = 10) -> float:
    n = len(scores)
    if n == 0:
        return 0.0
    ece = 0.0
    for b in reliability_bins(scores, correct, bins):
        ece += (b["n"] / n) * abs(b["confidence"] - b["accuracy"])
    return ece


def bootstrap_ci(values: Sequence[float], iters: int = 2000,
                 alpha: float = 0.05, seed: int = 0) -> Tuple[float, float]:
    """Percentile bootstrap confidence interval for the mean of ``values``.

    Pure standard library. Returns ``(lo, hi)`` for the ``1 - alpha`` interval
    (default 95%). With few samples the interval is honestly wide -- which is the
    point: it stops us reading noise as signal.
    """
    import random as _random
    vs = list(values)
    n = len(vs)
    if n == 0:
        return (0.0, 0.0)
    if n == 1:
        return (vs[0], vs[0])
    rng = _random.Random(seed)
    means = []
    for _ in range(iters):
        sample = [vs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int((alpha / 2.0) * iters)
    hi_idx = min(iters - 1, int((1.0 - alpha / 2.0) * iters))
    return (means[lo_idx], means[hi_idx])


def wilson_interval(successes: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion ``successes/total``.

    Appropriate when reporting a single run's escape/kill rate over a finite
    number of mutant trials, where a normal approximation is unreliable.
    """
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def summarize(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"n": 0, "mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}
    vs = sorted(values)
    n = len(vs)
    mean = sum(vs) / n
    median = vs[n // 2] if n % 2 else (vs[n // 2 - 1] + vs[n // 2]) / 2.0
    var = sum((v - mean) ** 2 for v in vs) / n
    return {"n": n, "mean": mean, "median": median, "min": vs[0], "max": vs[-1],
            "std": math.sqrt(var)}
