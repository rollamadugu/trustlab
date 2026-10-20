"""The trust metric predicts soundness on held-out verdicts far better than the
naive 'trust the green' baseline, and is reasonably calibrated. Fully seeded."""
import random

from trustlab.benchmark import build_modality, generate_all
from trustlab.metrics.stats import expected_calibration_error, roc_auc
from trustlab.trust.metric import naive_trust


def _auc_for(modality, seed=0):
    data = generate_all(seed)
    res = build_modality(modality, data[modality], seed=seed)
    test = [res.green[i] for i in res.test_idx]
    scores = [v.trust for v in test]
    labels = [1 if v.ground_truth_ok else 0 for v in test]
    return res.trust_auc, res.ece, roc_auc(scores, labels)


def test_trust_beats_naive_on_all_modalities():
    # naive trust gives every green the same score -> AUC == 0.5 (no ranking).
    for modality, floor in (("oracle", 0.68), ("heal", 0.90), ("judge", 0.90)):
        auc, ece, _ = _auc_for(modality, seed=0)
        assert auc > floor, f"{modality} trust AUC {auc} below {floor}"
        assert auc > 0.5


def test_trust_is_calibrated():
    for modality in ("oracle", "heal", "judge"):
        _, ece, _ = _auc_for(modality, seed=0)
        assert ece < 0.15, f"{modality} ECE {ece} too high"


def test_naive_trust_cannot_rank():
    data = generate_all(0)
    green = [v for v in data["judge"] if v.apparent_ok]
    scores = [naive_trust(v) for v in green]
    labels = [1 if v.ground_truth_ok else 0 for v in green]
    # all green get score 1.0 -> AUC degenerate at 0.5
    assert roc_auc(scores, labels) == 0.5


def test_trust_model_is_deterministic():
    a = _auc_for("heal", seed=1)[0]
    b = _auc_for("heal", seed=1)[0]
    assert a == b
