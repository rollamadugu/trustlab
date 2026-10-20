"""TrustLab — a measurement theory and experimental laboratory for the question:

    "When an AI says a software test PASSED, can we believe it?"

Modern teams increasingly let AI *generate* test oracles, *heal* broken UI
tests, and *adjudicate* pass/fail. Each can produce a GREEN result that is not
actually sound -- a *false pass* that creates false confidence. TrustLab:

  * grounds "soundness" in REAL mutation testing (injected faults = ground truth),
  * models the three AI-testing modalities (oracle / heal / adjudicate) so each
    emits a common `Verdict(apparent_ok, true_sound, trust, features)`,
  * defines a single, generalisable **trustworthiness metric** and the
    **False-Confidence Gap**, and
  * evaluates, with statistics and calibration (ECE), whether the trust metric
    can flag false passes better than naively trusting a green result.

Pure Python standard library (+ pytest for tests) so it runs on any laptop.
"""

__version__ = "0.1.0"
