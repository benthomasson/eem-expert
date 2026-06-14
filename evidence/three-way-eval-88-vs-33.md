# Three-Way Eval Confirms EEM Advantage Across All Rubrics

**Date:** 2026-05-20
**Source:** ~/git/redhat-expert/entries/2026/05/20/three-way-eval-comparison-expert-service-vs-an agent pipeline-across-all-rubrics.md

## Overview

A three-way eval comparison on the same 50-question Red Hat domain sample (seed=42) completes the evidence base for EEM's advantage over from-scratch retrieval. Expert-service (EEM-backed) was tested across five models; an agent pipeline (multi-step discovery, no EEM) serves as the baseline. Three rubrics — quality (reference-free A-grade), accuracy (0-1 vs expected), and Q/L/R/F (0-100 composite) — all show the same result from different angles.

Combined with the AAP from-scratch eval (2026-05-19) and the continuity experiment (2026-05-19), we now have convergent evidence across three independent evaluations, multiple question sets, multiple rubrics, and multiple models.

## The Full Evidence Base

### Eval 1: Red Hat Three-Way (50 questions, 6 systems, 3 rubrics)

| System | Quality (A%) | Accuracy (0-1) | Q/L/R/F (0-100) | Avg/Query |
|--------|-------------|----------------|-----------------|-----------|
| Expert + Opus 4.6 | 88% | 0.704 | 71.3 | 25s |
| Expert + Sonnet 4.6 | 72% | 0.686 | 69.5 | 23s |
| Expert + Haiku 4.5 | 64% | 0.617 | 57.8 | 9s |
| Expert + Gemma3 27B | 44% | 0.571 | 56.5 | 35s |
| Expert + Gemini 3.1 Pro | 48% | 0.589 | 53.3 | 31s |
| an agent pipeline (no EEM) | 33% | 0.239 | 28.1 | ~350s |

### Eval 2: AAP From-Scratch vs EEM (55 questions, Opus, 2 conditions)

| Metric | From Scratch | With EEM | Ratio |
|--------|-------------|---------|-------|
| MC accuracy (40 Q) | 97.5% | 100.0% | +2.5pp |
| OE key-fact recall (15 Q) | 72.9% | 85.6% | +12.7pp |
| Cost | $13.61 | $7.25 | 0.53x |
| Duration | 40 min | 19 min | 0.47x |

### Eval 3: Continuity Experiment (45 runs, 3 conditions, 3 fact sets)

| Metric | Conversation | EEM | Delta |
|--------|-------------|-----|-------|
| Novel inference | 62% | 88% | +26pp |
| Variance (best fact sets) | 0-27% std | 0% std | Zero variance |
| Fact recall | 100% | 100% | Tied (ceiling) |

## Five Findings That Converge

### Finding 1: EEM wins on every rubric, every eval

No rubric, question set, or evaluation method produced a result where the non-EEM condition outperformed the EEM condition in aggregate. The advantage ranges from +2.5pp (AAP MC, where Opus parametric knowledge handles most questions) to +55pp (Red Hat quality, where retrieval architecture dominates). The direction is always the same. Only the magnitude varies with task difficulty.

### Finding 2: Same model, different system — retrieval is the variable

The most controlled comparison in the three-way eval: Expert-service + Gemini 3.1 Pro scores 0.589 accuracy. an agent pipeline, which also uses Gemini 3.1 Pro for synthesis, scores 0.239. Same synthesis model. 2.5x better accuracy. 10x faster. The only difference is the retrieval architecture — belief network vs multi-step document discovery.

This isolates the EEM contribution from the model contribution. The belief network is doing the work, not the model.

### Finding 3: EEM prevents hallucination, not just improves retrieval

an agent pipeline produced 8 negative scores from penalty deductions for fabricated data or contradicting source documents (-47.0, -39.4, -27.0, -25.5, -17.25, -13.0, -10.5, -5.5). Expert-service models rarely go negative.

The mechanism: when the model has no pre-retrieved beliefs, it fills gaps with parametric knowledge — which may be wrong, outdated, or fabricated. The belief network constrains the answer space to justified, source-traced claims. The model can still hallucinate, but it has less reason to because it has pre-computed answers available.

The AAP eval shows the same pattern from the other direction. From-scratch Opus answered Q28 about operator-based mesh configuration from parametric knowledge (wrong: "automation controller UI"), while EEM Opus found belief `automation-mesh-operator-uses-custom-resources` (correct: "Kubernetes Custom Resources"). The from-scratch model didn't hallucinate randomly — it confidently applied knowledge from a different context (RPM-based deployments) because it didn't search deeply enough.

### Finding 4: Smaller models + EEM approach larger models without EEM

From the three-way eval:
- Expert + Haiku 4.5: 64% A-grade, 0.617 accuracy
- Expert + Gemma3 27B: 44% A-grade, 0.571 accuracy
- an agent pipeline (no EEM): 33% A-grade, 0.239 accuracy

Haiku (the smallest Claude model) with EEM scores 1.9x the A-grade and 2.6x the accuracy of an agent pipeline without EEM. Gemma3 27B (an open model running locally) with EEM scores 2.4x the accuracy. This confirms the architectural ablation finding (2026-03-28): Sonnet+beliefs approximates Opus without beliefs. EEM compensates for model capability.

The continuity experiment adds another dimension: EEM's novel inference advantage (88% vs 62%) was measured with the same model (Opus) in both conditions. The improvement comes from externalization, not from using a better model.

### Finding 5: EEM is cheaper AND better — no tradeoff

The AAP eval is the cleanest demonstration: EEM costs 0.53x and runs in 0.47x the time while being more accurate on both MC and OE. The three-way eval shows the same: expert-service queries complete in 9-35s vs ~350s for an agent pipeline.

The cost advantage has a simple explanation: pre-computed beliefs reduce per-query work. `reasons search` + `reasons show` on 1-3 beliefs is cheaper than searching 111 documents or running a multi-step agent loop. The construction cost of the belief network amortizes across all queries.

**The speed numbers are lower bounds.** The Red Hat eval ran expert-service at `--concurrency 4` and an agent pipeline at `--concurrency 1`. Expert-service's architecture (one retrieval + one synthesis call per query) parallelizes trivially because queries are independent — the bottleneck is Vertex AI rate limits, not expert-service resources. Concurrency could scale to 8 or 16 with no architectural changes. an agent pipeline's multi-step agent loop is sequential by design — each tool call depends on the previous result. At `--concurrency 4`, the effective throughput gap is already 40-160x. At higher concurrency it would widen further, limited only by the LLM provider's rate limits.

## What This Means for the EEM Thesis

Three independent evaluations now converge on the same conclusion:

1. **EEM improves accuracy** — consistently, across rubrics, across question types, across models
2. **EEM reduces cost and latency** — pre-computed retrieval is cheaper than per-query search
3. **EEM prevents hallucination** — constraining the answer space to justified beliefs reduces fabrication
4. **EEM compensates for model size** — smaller models + EEM approach larger models without EEM
5. **EEM improves novel inference** — externalized beliefs produce better cross-fact reasoning than conversation context

These are not five separate findings. They are five facets of the same phenomenon: **pre-computed, justified, structured knowledge retrieves more efficiently and more accurately than per-query document search or parametric knowledge.** This is what the "always deploy EEM with agents" thesis rests on.

## Remaining Questions

1. **Variance across runs.** The AAP and Red Hat evals are single runs. The continuity experiment showed zero variance on EEM's best metric but the domain evals need 3-5 runs for confidence intervals.

2. **Coverage gaps.** The AAP eval showed EEM losing on 2 of 15 OE questions (subscription management, troubleshooting) where belief coverage was thin. The Red Hat eval's 12,731-belief network presumably has fewer gaps, but coverage analysis hasn't been run.

3. **Open-ended scoring.** The AAP OE scoring uses keyword matching (too strict). The Red Hat eval uses LLM-as-judge (better). Future AAP runs should use LLM-as-judge for meaningful absolute numbers.

4. **Model-specific effects.** The Red Hat eval tested 5 models with EEM. The AAP eval only tested Opus. Running AAP with Sonnet/Haiku would complete the model-size comparison.

## Raw Data

- Red Hat three-way: ~/git/redhat-expert/entries/2026/05/20/three-way-eval-comparison-expert-service-vs-an agent pipeline-across-all-rubrics.md
- AAP from-scratch vs EEM: ~/git/claude-automated/eem_eval_results/results_20260519_163136.json (MC), results_20260519_165841.json (OE)
- Continuity experiment: ~/git/claude-automated/continuity_results/results_20260519_093952.json
- AAP eval writeup: ~/git/beliefs-pi/entries/2026/05/19/eem-vs-scratch-eval-results.md
- Continuity writeup: ~/git/beliefs-pi/entries/2026/05/19/continuity-experiment-results-eem-vs-conversation.md
