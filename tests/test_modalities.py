"""Each modality emits a common Verdict with a real ground-truth label and
observable features, and each genuinely produces false passes."""
import random

from trustlab.modalities import (generate_adjudication_verdicts,
                                  generate_healing_verdicts,
                                  generate_oracle_verdicts)
from trustlab.trust.metric import false_confidence_gap


def test_oracle_verdicts_are_green_and_grounded_in_mutation_score():
    vs = generate_oracle_verdicts(random.Random(1))
    assert vs
    assert all(v.apparent_ok for v in vs)          # a well-formed suite is green
    assert all("mutation_score" in v.info for v in vs)
    assert all("exact_coverage" in v.features for v in vs)
    assert 0.3 < false_confidence_gap(vs) < 0.9     # weak AI suites -> false passes


def test_healing_has_silent_mispasses_and_confidence_signal():
    vs = generate_healing_verdicts(random.Random(2), n=600)
    green = [v for v in vs if v.apparent_ok]
    fp = [v for v in green if v.false_pass]
    assert fp, "expected some silent mis-heals"
    good = [v.features["match_confidence"] for v in green if not v.false_pass]
    bad = [v.features["match_confidence"] for v in fp]
    # correct heals should, on average, be more confident than silent mis-heals
    assert sum(good) / len(good) > sum(bad) / len(bad)


def test_adjudication_produces_false_passes_with_consistency_feature():
    vs = generate_adjudication_verdicts(random.Random(3), n=600)
    green = [v for v in vs if v.apparent_ok]
    assert any(v.false_pass for v in green)
    assert all("consistency" in v.features for v in vs)


def test_verdict_false_pass_semantics():
    vs = generate_healing_verdicts(random.Random(4), n=50)
    for v in vs:
        assert v.false_pass == (v.apparent_ok and not v.ground_truth_ok)
