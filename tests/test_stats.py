"""Statistics behave correctly on known inputs."""
from trustlab.metrics.stats import (a12_magnitude, expected_calibration_error,
                                     mann_whitney_u, reliability_bins, roc_auc,
                                     vargha_delaney_a12)


def test_roc_auc_perfect_and_inverse():
    assert roc_auc([0.9, 0.8, 0.7], [1, 1, 1]) != roc_auc  # sanity: callable result
    assert roc_auc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) == 1.0
    assert roc_auc([0.1, 0.2, 0.8, 0.9], [1, 1, 0, 0]) == 0.0
    assert roc_auc([0.5, 0.5], [1, 0]) == 0.5


def test_mann_whitney_separation():
    _, p = mann_whitney_u([10, 11, 12, 13, 14], [1, 2, 3, 4, 5])
    assert p < 0.05


def test_a12_extremes():
    assert vargha_delaney_a12([9, 9, 9], [1, 1, 1]) == 1.0
    assert vargha_delaney_a12([1, 2, 3], [1, 2, 3]) == 0.5
    assert a12_magnitude(1.0) == "large"
    assert a12_magnitude(0.5) == "negligible"


def test_ece_calibrated_vs_miscalibrated():
    good = expected_calibration_error([0.9] * 10, [1] * 9 + [0], bins=5)
    bad = expected_calibration_error([0.99] * 10, [0] * 10, bins=5)
    assert good < 0.05
    assert bad > 0.9


def test_reliability_bins_cover_all_points():
    bins = reliability_bins([0.1, 0.4, 0.9], [0, 1, 1], bins=10)
    assert sum(b["n"] for b in bins) == 3
