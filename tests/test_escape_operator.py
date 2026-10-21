import random

from trustlab.modalities.oracles import escape_counts_by_operator


def test_escape_counts_structure_and_bounds():
    counts = escape_counts_by_operator(random.Random(1), suites_per_subject=4, n_tests=8)
    assert counts, "should find at least one mutation-operator class"
    for op, c in counts.items():
        assert op in {"AOR", "ROR", "LCR", "CRP", "UOD"}
        assert c["total"] > 0
        assert 0 <= c["killed"] <= c["total"]


def test_escape_counts_deterministic_with_seed():
    a = escape_counts_by_operator(random.Random(3), suites_per_subject=4, n_tests=8)
    b = escape_counts_by_operator(random.Random(3), suites_per_subject=4, n_tests=8)
    assert a == b
