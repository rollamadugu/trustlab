# Pre-registration — real-tool runs

This document fixes the analysis **before** the real-tool experiments are run, so
the results cannot be shaped after the fact. It is committed ahead of the run.
(Prompted by reviewer feedback on the write-up: pre-declare pass/fail criteria
and report uncertainty.)

## Scope

Replacing a *modelled* modality with a *real* tool behind the existing adapter
seam (`generate_*_verdicts` → `Verdict`), without changing the trust metric or
the experiments.

### Run A — real LLM-as-judge

- **Tool:** a real LLM (local via Ollama, or an API model) used to adjudicate
  pass/fail on program outputs, replacing `generate_adjudication_verdicts`.
- **Ground truth:** unchanged — an output is sound iff it matches the reference
  program's output (the same mutation-grounded oracle used elsewhere).
- **Sample size:** at least 1,000 green verdicts across the existing subjects,
  ≥ 10 seeds.

### Run B — real self-healing

- **Tool:** a real locator self-healer (e.g. a Playwright/Selenium healing
  strategy) on a mutated DOM, replacing `generate_healing_verdicts`.
- **Ground truth:** whether the healed locator resolves to the originally
  intended element.

## Hypotheses (directional, fixed in advance)

- **H1.** The real tool exhibits a non-zero False-Confidence Gap (some green
  verdicts are false passes). *Falsified if the 95% CI for FCG includes 0.*
- **H2.** The calibrated trust metric separates sound from false-pass verdicts
  better than the naive "trust any green" baseline. *Success criterion: trust
  ROC-AUC 95% CI lower bound > 0.50.*
- **H3.** Gating at a fixed retention (accept the top 70% most-trusted green
  verdicts) reduces the false-pass rate versus no gating.

## Pass/fail and reporting rules (fixed in advance)

1. Report **95% confidence intervals** for every headline number (bootstrap
   across seeds; Wilson interval for single-run proportions). A difference is
   only claimed if the intervals do not overlap.
2. Report **escape rate broken down by fault class** (mutation operator), not
   only a combined figure.
3. Report the real-tool numbers **separately** from any modelled numbers; never
   combine them into a single headline.
4. Publish the exact tool, version, prompt/config, and seeds with the results.
5. Negative results (e.g. the metric fails H2 for a real tool) will be reported
   as-is.

## Status

Not yet run. Results will be added under `results/` with the tool and config
recorded, and this document will be linked from the run.
