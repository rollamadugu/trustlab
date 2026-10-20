# PhD Research Proposal

**Working title:** *Trust in AI-Driven Software Testing: A Measurement Theory and
Empirical Study of When AI-Generated, AI-Healed, and AI-Adjudicated Test Verdicts
Can Be Believed.*

**Candidate fit:** 11 years of enterprise test-automation practice (Java/Python;
Selenium, Playwright, Cypress, Katalon; API/DB/CI) across regulated MNC domains
(airline, healthcare, banking). The research question is drawn directly from that
practice, so the candidate can both motivate it from the field and explain every
part of it without borrowing vocabulary from an unfamiliar discipline.

---

## 1. Problem

Software teams now let AI do three things that used to be human-owned:
**generate** test oracles/assertions, **heal** broken UI-test locators, and
**adjudicate** pass/fail (LLM-as-judge, flaky-vs-real triage). Each can return a
**GREEN** result that is not actually sound — a *false pass* that creates false
confidence: an assertion too weak to catch the bug, a locator healed onto the
wrong element, a hallucinated "it passed". Teams increasingly *ship on these
green results*. The field has rushed to build these AI mechanisms but has not
answered the prior question: **when the AI says a test passed, can we believe
it, and with what confidence?**

## 2. Gap (what the literature does not provide)

Recent work confirms the symptom but not a cure. A 2026 systematic review of LLM
test oracles (2,436 records screened) finds oracle quality is judged by
*resemblance to a known oracle*, not by *whether injected faults are caught*, and
that "LLM-as-a-judge" names *how* a verdict is produced, not *why* it should be
trusted. Companion studies show LLM oracles mostly echo implemented behaviour
(so they miss real bugs); autonomous test-repair produces "misleading outcomes"
under unconstrained autonomy; ML flaky-test classifiers "lack generalizability";
and agentic web-test agents "hallucinate" verdicts. Every result is the same
unmet need: **a principled, measurable, calibrated notion of trust in an AI test
verdict — and it is studied, if at all, one mechanism at a time, never unified.**

## 3. Thesis statement

*AI-driven testing produces a large, measurable False-Confidence Gap that varies
by modality and by code structure; and a single, calibrated trustworthiness
metric, computed from observable signals alone, can predict which green verdicts
are sound far better than the industry-default "trust the green" — generalising
across oracle generation, self-healing, and adjudication.*

## 4. Research questions and hypotheses

* **RQ1 (phenomenon):** How large is the False-Confidence Gap (fraction of green
  verdicts that are false passes), and how does it vary by modality and by the
  code under test? **H1:** it is large and systematic, not incidental.
* **RQ2 (metric):** Can a trustworthiness metric computed from observable signals
  rank sound greens above false passes far better than naive trust? **H2:** yes,
  ROC-AUC well above 0.5 across all three modalities.
* **RQ3 (calibration):** Can the trust score be used as a probability? **H3:** yes,
  with low Expected Calibration Error.
* **RQ4 (operational value):** Does accepting only high-trust greens cut the
  false-pass rate at a reasonable retention? **H4:** yes, substantially.
* **RQ5 (generality):** Does one metric framework instantiate across all three
  modalities? **H5:** yes, via per-modality observable feature views.

## 5. Method

Soundness is grounded in **real mutation testing** (injected faults = objective
ground truth), so "trustworthy" is never a matter of opinion. Each modality is
reduced to a common `Verdict(apparent_ok, ground_truth_ok, features)`; the trust
metric is a small, interpretable, *calibratable* model over **observable**
features only (never ground truth); evaluation uses held-out splits, ROC-AUC,
Mann-Whitney U, Vargha-Delaney A12, and ECE.

## 6. Preliminary results (already implemented and evaluated — "TrustLab")

A working prototype runs on a laptop (pure Python; real AST mutation engine; 6
subject programs; three modalities; trained trust model). Over 15 seeds:

| Modality | False-Confidence Gap | Trust ROC-AUC (vs naive 0.50) | ECE | False-pass rate: naive -> trust (top-70% accepted) |
|---|---|---|---|---|
| AI-generated oracles | **61.9%** | **0.757** (A12 0.76, p<0.001) | 0.076 | 61% -> 50% |
| AI self-healing | **10.8%** | **0.947** (A12 0.95, p<0.001) | 0.042 | 11% -> **0.5%** |
| AI adjudication | **40.7%** | **0.944** (A12 0.94, p<0.001) | 0.045 | 40% -> **19%** |

A genuine secondary finding: the oracle False-Confidence Gap tracks **code
structure** — branch-heavy subjects (`grade` 99.7%, `triangle_type` 93.6%,
`discount` 81.5%) are far more dangerous than simple ones (`classify_bmi` 5.2%).
A released labelled benchmark of 2,000+ verdicts accompanies the results.

## 7. Contributions

1. The **False-Confidence Gap** — a defined, measured phenomenon across three AI-
   testing modalities (not "I built a tool").
2. A **unified, calibrated trustworthiness metric** over observable signals,
   validated against mutation-testing ground truth.
3. An **operational trust-gating policy** that cuts false passes at bounded cost.
4. A **released benchmark** of labelled AI-testing verdicts (a citable artefact).
5. (Thesis extensions) real-LLM/real-Playwright adapters; cross-project
   generalisation; regulated-domain case studies (finance/healthcare).

## 8. Why this is research, not a POC

It opens with a *measured phenomenon* and a *falsifiable claim*, grounds truth in
mutation testing, compares against a baseline with statistics and calibration,
generalises across three modalities, and leaves behind a metric and a benchmark
others can cite. The engineering demo is merely the evidence.

## 9. Evaluation plan (thesis) and venues

Scale subjects (Defects4J-style real bugs), add real LLM oracle generators and a
real Playwright self-healer via the existing adapter seam, add cross-project
generalisation and regulated-domain case studies, and a user study on whether
trust scores change practitioner decisions. Target venues: ICSE, FSE/ESEC, ASE,
ISSTA, ISSRE, EMSE/TOSEM.
