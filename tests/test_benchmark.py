"""The benchmark builds a labelled corpus across all three modalities with the
expected shape and a meaningful False-Confidence Gap and trust AUC."""
from trustlab.benchmark import build_benchmark


def test_benchmark_shape_and_results():
    results, payload = build_benchmark(seed=0)
    assert set(results) == {"oracle", "heal", "judge"}
    summ = payload["summary"]["modalities"]
    for m in ("oracle", "heal", "judge"):
        assert summ[m]["false_confidence_gap"] > 0.0
        assert summ[m]["trust_auc"] > 0.5
        assert summ[m]["n_green"] > 0
    # the corpus records carry label + trust + features + split
    rec = payload["verdicts"][0]
    for key in ("modality", "apparent_ok", "ground_truth_ok", "false_pass",
                "trust", "features", "split"):
        assert key in rec


def test_benchmark_is_reproducible():
    _, a = build_benchmark(seed=0)
    _, b = build_benchmark(seed=0)
    assert a["summary"] == b["summary"]
