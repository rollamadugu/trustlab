import random

from trustlab.metrics.stats import bootstrap_ci, wilson_interval


def test_bootstrap_ci_brackets_the_mean():
    vals = [0.60, 0.61, 0.62, 0.59, 0.63, 0.60, 0.62]
    mean = sum(vals) / len(vals)
    lo, hi = bootstrap_ci(vals, seed=1)
    assert lo <= mean <= hi
    assert lo <= hi


def test_bootstrap_ci_constant_is_degenerate():
    lo, hi = bootstrap_ci([0.5, 0.5, 0.5, 0.5], seed=1)
    assert lo == hi == 0.5


def test_bootstrap_ci_single_value():
    assert bootstrap_ci([0.42]) == (0.42, 0.42)


def test_bootstrap_ci_empty():
    assert bootstrap_ci([]) == (0.0, 0.0)


def test_bootstrap_ci_is_deterministic_with_seed():
    vals = [random.Random(0).random() for _ in range(20)]
    assert bootstrap_ci(vals, seed=5) == bootstrap_ci(vals, seed=5)


def test_wilson_interval_bounds():
    lo, hi = wilson_interval(8, 10)
    assert 0.0 <= lo <= 0.8 <= hi <= 1.0


def test_wilson_interval_all_success():
    lo, hi = wilson_interval(10, 10)
    assert hi == 1.0 or hi > lo
    assert lo < 1.0


def test_wilson_interval_zero_total():
    assert wilson_interval(0, 0) == (0.0, 0.0)
