"""The rigorous core: mutation testing produces real ground-truth faults, and a
strong oracle kills them while a weak one does not."""
from trustlab.sut.programs import SUBJECTS, subject_by_name
from trustlab.sut.mutation import generate_mutants, mutation_score


def test_mutants_generated_for_every_subject():
    for s in SUBJECTS:
        muts = generate_mutants(s)
        assert muts, f"no mutants for {s.name}"
        assert all(m.func is not None for m in muts), "all mutants should compile"


def test_triangle_has_many_nonequivalent_mutants():
    muts = generate_mutants(subject_by_name("triangle_type"))
    nonequiv = [m for m in muts if not m.equivalent]
    assert len(nonequiv) >= 8


def test_strong_oracle_kills_weak_oracle_misses():
    s = subject_by_name("grade")
    ref = s.compile_ref()
    muts = generate_mutants(s)

    def strong(mut):
        return any(_safe(mut, a) != _safe(ref, a) for a in s.inputs)

    def weak(mut):  # only notices a type change / exception
        for a in s.inputs:
            r = _safe(mut, a)
            if isinstance(r, Exception) or type(r) is not type(_safe(ref, a)):
                return True
        return False

    strong_ms = mutation_score(strong, muts)
    weak_ms = mutation_score(weak, muts)
    assert strong_ms >= 0.9
    assert weak_ms <= 0.1
    assert strong_ms > weak_ms


def test_equivalent_mutants_are_flagged():
    # some subjects legitimately produce equivalent mutants; the flag must exist
    any_equiv = False
    for s in SUBJECTS:
        if any(m.equivalent for m in generate_mutants(s)):
            any_equiv = True
    assert any_equiv


def _safe(f, args):
    try:
        return f(*args)
    except Exception as e:  # noqa
        return e
