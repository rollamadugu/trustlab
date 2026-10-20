# Contributing to TrustLab

Thanks for your interest. TrustLab is a research prototype exploring **trust and
measurement in AI-driven software testing**. Contributions, replications, and
critical feedback are all welcome — especially attempts to break the findings.

## Ways to contribute

- **Replicate** the experiments on your machine and report whether the numbers hold.
- **Add a subject program** under `trustlab/sut/programs.py` (with a reference
  implementation) to broaden the mutation-testing ground truth.
- **Plug in a real tool** behind the adapter seam: a real Playwright/Selenium
  self-healer or a real LLM judge, replacing the modelled `generate_*_verdicts`
  while keeping the `Verdict` interface, so the trust metric and experiments run
  unchanged.
- **Strengthen the statistics** or calibration analysis.
- **Challenge the methodology** — open an issue describing where the design or a
  claim might be wrong.

## Development setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest            # 19 tests should pass
```

Pure Python standard library only for the core (plus `pytest` for tests). Please
keep new core code dependency-free where practical.

## Pull requests

1. Fork and create a feature branch.
2. Add or update tests for any behaviour change.
3. Make sure `pytest` passes.
4. Open a PR describing the change and its motivation.

## Code of conduct

Be respectful and constructive. Assume good faith. This is a learning and
research space.
