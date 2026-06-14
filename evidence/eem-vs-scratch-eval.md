# EEM vs From-Scratch Eval Results (Corrected)

**Date:** 2026-05-19
**Continues:** entries/2026/05/19/continuity-experiment-results-eem-vs-conversation.md

## Setup

Two conditions on the same 55-question set (40 MC + 15 open-ended) about Ansible Automation Platform 2.6:

**From scratch:** `claude -p` in a workdir with 111 AAP source documents (2.4MB markdown). The model searches and reads docs to answer. No EEM.

**With EEM:** `claude -p` in a workdir with a 390-belief reasons.db (360 IN / 30 OUT). The model queries beliefs via `reasons search` / `reasons show`. No source documents.

Both used Opus, same question set, same `--output-format json` for token tracking. Questions from the expert-service eval suite (40 MC with choices + correct letter, 15 open-ended with key-fact rubrics).

**Important correction:** The first run (results_20260519_141726.json) was invalid — 62.5% of EEM queries had `reasons` CLI calls denied by `claude -p` sandboxing. The model fell back to parametric knowledge, making the EEM condition appear slower and more expensive than it actually is. The corrected run uses `--allowedTools "Bash(reasons *)"` to grant proper tool access. All results below are from the corrected run.

## Results

### Multiple Choice (40 questions)

| Metric | From Scratch | With EEM |
|--------|-------------|---------|
| **Accuracy** | **39/40 (97.5%)** | **40/40 (100.0%)** |
| Total tokens | 30,965 | 8,330 |
| Total cost | $4.36 | $2.42 |
| Mean latency | 13.8s | 6.1s |
| Total duration | 552s (9.2min) | 243s (4.1min) |
| Cost per question | $0.109 | $0.061 |
| Tokens per question | 774 | 208 |

**Disagreements (1 of 40):**

- **Q28** ("How is automation mesh configured in operator-based deployments?"): From-scratch answered c (automation controller UI), EEM answered b (Kubernetes Custom Resources, correct). The EEM model found belief `automation-mesh-operator-uses-custom-resources` with the exact answer. The from-scratch model conflated the UI-based RPM workflow with the operator-based approach.

### Open-Ended (15 questions)

Key-fact recall scoring (keyword matching against rubric's key_facts list):

| Metric | From Scratch | With EEM |
|--------|-------------|---------|
| **Mean key-fact recall** | **72.9%** | **85.6%** |
| Total tokens | 111,430 | 41,869 |
| Total cost | $9.25 | $4.83 |
| Mean latency | 123.9s | 59.3s |
| Total duration | 1,859s (31min) | 889s (14.8min) |

**Per-question comparison:**

| Question | Scratch | EEM | Delta |
|----------|---------|-----|-------|
| OE1 (installation overview) | 60% | 100% | +40pp |
| OE2 (mesh architecture) | 100% | 100% | — |
| OE3 (RBAC model) | 67% | 83% | +17pp |
| OE4 (execution environments) | 75% | 75% | — |
| OE5 (credential management) | 100% | 100% | — |
| OE6 (high availability) | 40% | 100% | +60pp |
| OE7 (upgrade process) | 83% | 100% | +17pp |
| OE8 (collections & content) | 80% | 80% | — |
| OE9 (backup/restore) | 80% | 80% | — |
| OE10 (upgrade vs migration) | 80% | 100% | +20pp |
| OE11 (platform components) | 50% | 100% | +50pp |
| OE12 (mesh topology) | 83% | 100% | +17pp |
| OE13 (subscription management) | 75% | 25% | -50pp |
| OE14 (troubleshooting) | 60% | 40% | -20pp |
| OE15 (security hardening) | 60% | 100% | +40pp |

EEM won on 8 questions, tied on 5, lost on 2. The two EEM losses (OE13, OE14) suggest the belief network may have gaps in subscription management and troubleshooting topics — areas where direct document search can find specific procedural details that weren't distilled into beliefs.

### Combined Cost Summary

| Metric | From Scratch | With EEM | Ratio |
|--------|-------------|---------|-------|
| Total cost (55 questions) | $13.61 | $7.25 | **0.53x** |
| Total duration | 2,411s (40min) | 1,132s (19min) | **0.47x** |
| MC accuracy | 97.5% | 100.0% | +2.5pp |
| OE key-fact recall | 72.9% | 85.6% | +12.7pp |

## Analysis

### Finding 1: EEM is cheaper, faster, AND more accurate

This is the headline result and it reverses the initial (invalid) finding. With proper tool access:
- **1.9x cheaper** ($7.25 vs $13.61)
- **2.1x faster** (19min vs 40min)
- **More accurate** on both MC (+2.5pp) and OE (+12.7pp)

The cost advantage comes from the fundamental asymmetry: the from-scratch model must search and read through 111 source documents (2.4MB) to find relevant information, generating 30,965 tokens on MC and 111,430 on OE. The EEM model runs `reasons search "query"`, gets a ranked list of relevant beliefs, and reads 1-3 specific beliefs — generating only 8,330 tokens on MC and 41,869 on OE.

### Finding 2: The first run's results were completely wrong

The initial run showed EEM as 3.1x more expensive and 2.6x slower than from-scratch. This was an artifact of `claude -p` sandboxing denying 62.5% of `reasons` CLI calls. When tool calls were denied, the model fell back to parametric knowledge with verbose explanations (trying to compensate for not having source data), producing higher token counts and costs.

The lesson: **always verify that tool-using conditions actually use their tools.** Permission denials are silent failures that produce plausible-looking but invalid results.

### Finding 3: EEM's advantage is largest on knowledge-dense questions

The biggest EEM wins were on questions requiring recall of multiple specific facts:
- OE6 (high availability): +60pp — EEM found all HA-specific beliefs; scratch only found 2/5 facts in the docs
- OE11 (platform components): +50pp — EEM had pre-indexed component relationships
- OE1 (installation overview): +40pp — EEM's belief structure mirrors the installation taxonomy
- OE15 (security hardening): +40pp — security facts were well-captured as individual beliefs

### Finding 4: EEM has coverage gaps on procedural and edge topics

The two questions where scratch outperformed EEM:
- OE13 (subscription management): scratch 75% vs EEM 25% (-50pp) — subscription details may not have been captured as beliefs during construction
- OE14 (troubleshooting): scratch 60% vs EEM 40% (-20pp) — troubleshooting procedures are procedural knowledge that's harder to capture as declarative beliefs

This suggests that belief construction coverage matters. The 390-belief network covers the core architecture well but has gaps in operational procedures. This is addressable by adding more beliefs or by hybrid retrieval (EEM + source fallback).

### Finding 5: Token efficiency explains the cost advantage

On MC questions, EEM used 208 tokens/question vs scratch's 774 tokens/question — a 3.7x token efficiency advantage. On OE questions, the ratio was even larger: 2,791 vs 7,429 tokens/question (2.7x).

The mechanism is straightforward: `reasons search "query"` returns a ranked list of belief IDs with scores. The model then calls `reasons show <id>` on 1-3 top results to get the full belief text. This is 2-3 tool calls total. From-scratch must use `Grep`, `Glob`, and `Read` across 111 files, often reading multiple documents before finding the relevant information.

### Finding 6: The from-scratch model sometimes answers without searching

Several scratch answers had suspiciously low latency (4-7s) and token counts (~190-260 tokens). These are questions where Opus answered from parametric knowledge without searching the source docs — it recognized the AAP topic and answered from training data. This works when parametric knowledge is correct (most questions) but fails on version-specific details (Q28).

EEM doesn't have this shortcut — every answer goes through `reasons search`. This is a feature, not a bug: the belief network is version-specific and authoritative, while parametric knowledge may be stale or incorrect for specific version details.

## Comparison: Corrected vs Initial Run

| Metric | Initial (broken) | Corrected | What changed |
|--------|------------------|-----------|-------------|
| MC: Scratch | 95.0% (38/40) | 97.5% (39/40) | Non-deterministic |
| MC: EEM | 97.5% (39/40) | **100.0% (40/40)** | Tool access fixed |
| Cost ratio | EEM 3.1x more | **EEM 0.53x (47% cheaper)** | Reversed |
| Speed ratio | EEM 2.6x slower | **EEM 0.47x (53% faster)** | Reversed |
| OE recall: Scratch | 6.8% | 72.9% | Scoring also improved |
| OE recall: EEM | 14.6% | 85.6% | Both better with tools |

The initial run's cost/speed reversal is entirely explained by permission denials. The accuracy numbers are closer because the model's parametric knowledge is decent on this domain — but the cost and speed advantages of EEM only appear when it can actually query the belief network.

## Comparison to Prior Results

| Eval | From Scratch | With EEM | Delta |
|------|-------------|---------|-------|
| **This eval (Opus, 40 MC)** | 97.5% | **100.0%** | +2.5pp |
| **This eval (Opus, 15 OE recall)** | 72.9% | **85.6%** | +12.7pp |
| Expert-service eval (Opus, 50 Q) | 33% A-grade | 88% A-grade | +55pp |
| Haiku dual-path (50 Q) | — | 94% A+B | — |
| Architectural ablation (4 models) | — | +12-14pp | — |

The smaller MC gap (+2.5pp vs +55pp in expert-service) reflects that Opus's parametric knowledge handles most AAP MC questions correctly. The expert-service eval used more complex questions and full LLM-as-judge scoring, which penalizes incomplete or poorly-structured answers more heavily. The OE recall gap (+12.7pp) is closer to the expert-service finding and better reflects EEM's advantage on knowledge completeness.

## Connection to Existing Threads

- **`construction-cost-dominates-retrieval-cost`** — strongly confirmed. EEM retrieval is not just cheap, it's *cheaper than from-scratch*. The construction cost of the 390-belief network is a one-time investment that produces a query-time cost advantage.
- **`eem-validated-remaining-work-is-accessibility`** — this eval confirms EEM works with Opus and is cost-effective. The `--allowedTools` discovery is directly relevant to accessibility: tooling friction matters.
- **`rag-is-semantic-not-epistemic`** — from-scratch is essentially RAG over source docs. EEM's structured, pre-distilled beliefs retrieve more efficiently because the relevance filtering happened during construction, not at query time.

## Methodological Note: Verify Tool Access

The most important lesson from this eval: **always verify that tool-using experimental conditions actually use their tools.** The `claude -p` sandbox silently denies unrecognized CLI calls, producing results that look valid but measure the wrong thing. The `--allowedTools` flag is required for any condition that uses custom CLIs.

Signs of silent tool denial:
- Higher-than-expected token counts (model compensates with verbose parametric answers)
- Shorter-than-expected latencies on some questions (no tool call overhead)
- The model says "Based on the belief network..." but doesn't quote specific beliefs or node IDs
- `permission_denials` field in `--output-format json` output

## Next Steps

1. **Run with Sonnet/Haiku** — smaller models should get a bigger EEM advantage (confirmed by prior architectural ablation and Haiku dual-path results)
2. **Use LLM-as-judge for open-ended** — keyword matching is too strict for absolute scores, though relative comparisons are valid
3. **Fill EEM coverage gaps** — add beliefs for subscription management and troubleshooting to address OE13/OE14 weakness
4. **Multiple runs for variance** — this was a single run; need 3-5 for confidence intervals
5. **Hybrid condition** — EEM + source document fallback, to get the speed of EEM with the coverage of full docs

## Raw Data

- Corrected MC results: `~/git/claude-automated/eem_eval_results/results_20260519_163136.json`
- Corrected OE results: `~/git/claude-automated/eem_eval_results/results_20260519_165841.json`
- Invalid first MC run: `~/git/claude-automated/eem_eval_results/results_20260519_141726.json` (62.5% tool denials)
- Invalid first OE run: `~/git/claude-automated/eem_eval_results/results_20260519_152846.json`
- Harness: `~/git/claude-automated/test_eem_vs_scratch.py`
- Questions: `~/git/expert-service/eval/questions.json`, `open_ended.json`
- Source docs: `~/git/aap-expert/sources/` (111 files, 2.4MB)
- EEM: `~/git/aap-expert/reasons.db` (390 beliefs, 360 IN / 30 OUT)
