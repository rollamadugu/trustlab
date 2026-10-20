# Thesis Outline & Paper Plan

**Title:** *Trust in AI-Driven Software Testing: A Measurement Theory and Empirical
Study of When AI-Generated, AI-Healed, and AI-Adjudicated Test Verdicts Can Be
Believed.*

The thesis is organised so each core chapter is also a publishable paper. The
"prototype status" column marks what already exists in this repository (TrustLab)
versus what is thesis-stage extension.

---

## Ch.1 Introduction & the False-Confidence problem
Motivation from industrial practice (AI generate/heal/adjudicate in CI), the
"trust the green" default, and the thesis statement. *Prototype: proposal + demo.*

## Ch.2 Background & Systematic Literature Review
Oracle problem, mutation testing, self-healing locators, flaky tests, LLM-as-
judge, calibration/trustworthy ML. PRISMA review establishing the gap that trust
is studied per-mechanism and judged by resemblance, not fault-detection.
*Thesis-stage (protocol reusable from the embedded project).*

## Ch.3 A measurement theory of verdict trust  — **Paper 1**
Formal definitions: `Verdict`, *false pass*, **False-Confidence Gap (FCG)**,
trustworthiness label grounded in mutation testing, and the trust metric as a
calibrated probability over observable signals. *Prototype: `trustlab/verdict.py`,
`trustlab/trust/metric.py`, `trustlab/sut/mutation.py`.*

## Ch.4 The False-Confidence Gap across modalities  — **Paper 2 (empirical)**
Measures FCG for AI-generated oracles, self-healing, and adjudication; shows it is
large (11%–62%) and structure-dependent (branch-heavy code is far more dangerous).
*Prototype: `experiments/exp1_false_confidence_gap.py`; result: oracle 61.9%,
heal 10.8%, judge 40.7%; per-subject oracle breakdown.*

## Ch.5 A unified, calibrated trust metric  — **Paper 3 (method + evaluation)**
One metric framework, per-modality observable feature views; held-out ROC-AUC,
A12, Mann-Whitney, ECE; operational trust-gating. *Prototype:
`experiments/exp2_trust_metric.py`; result: AUC 0.76/0.95/0.94, ECE <0.08,
false-pass 11%->0.5% (heal), 40%->19% (judge).*

## Ch.6 Benchmark & reproducibility  — **artefact paper / dataset track**
A released labelled corpus of AI-testing verdicts + harness. *Prototype:
`trustlab/benchmark.py` -> `results/trust_benchmark.json` (2,000+ records).*

## Ch.7 From model to the real world  — **Paper 4**
Swap the modality models for real components via the adapter seam: a real LLM
oracle generator, a real Playwright self-healer, a real LLM judge; confirm the
FCG and the trust metric transfer. *Thesis-stage; adapter boundary already
isolated behind `generate_*_verdicts` + `Verdict`.*

## Ch.8 Generalisation & regulated-domain case studies  — **Paper 5**
Cross-project generalisation of the trust model; case studies in finance/
healthcare CI (the candidate's domains); optional practitioner user study on
whether trust scores change ship/no-ship decisions. *Thesis-stage.*

## Ch.9 Threats, limitations, ethics
Simulator fidelity, equivalent mutants, generalisability of feature views, and
the risk of over-trusting the trust metric itself (meta-calibration).

## Ch.10 Conclusions & future work
A trust layer for AI testing pipelines; standards implications for safety- and
compliance-critical software.

---

### Mapping contributions → chapters → artefacts
| Contribution | Chapter | Artefact in repo |
|---|---|---|
| FCG defined & measured | 3,4 | exp1, mutation engine |
| Unified calibrated trust metric | 3,5 | trust/metric.py, exp2 |
| Operational trust-gating | 5 | exp2 (_operational) |
| Released benchmark | 6 | benchmark.py, results/*.json |
| Real-component transfer | 7 | adapter seam (modalities/) |

### Suggested 4–5 year schedule
Y1 review + Ch.3/Paper 1. Y2 Ch.4/Paper 2 + Ch.5/Paper 3. Y3 benchmark + Ch.7/
Paper 4. Y4 Ch.8/Paper 5 + generalisation. Y5 integration, user study, writing.
