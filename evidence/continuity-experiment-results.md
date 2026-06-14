# Continuity Experiment Results: EEM vs Conversation

**Date:** 2026-05-19
**Continues:** entries/2026/05/19/continuity-experiment-design-eem-vs-conversation.md

## Setup

Three conditions, three fact sets, five runs each (45 total experiments). Each run: establish 5 domain facts, correct 2, derive a cross-reference, test recall. All runs used Opus via `claude -p` with `--output-format json` for token tracking.

**Condition A:** Conversation continuity (`claude -c` across steps)
**Condition B:** EEM continuity (fresh sessions with reasons.db + checkpoint.md + CLAUDE.md)
**Condition C:** Conversation under compaction stress (`-c` with inline noise injection between derive and test)

Fact sets: software project (tech stack, team, deploy process), business operations (revenue, budget, org), scientific experiment (catalyst, temperature, yield).

## Results

### Accuracy (mean ± std across 15 runs per condition)

| Metric | Cond A | Cond B (EEM) | Cond C |
|--------|--------|-------------|--------|
| Fact recall (out of 5) | 5.00 ± 0.00 | 5.00 ± 0.00 | 5.00 ± 0.00 |
| Correction persistence (out of 2) | 2.00 ± 0.00 | 2.00 ± 0.00 | 2.00 ± 0.00 |
| Stale facts used | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Hallucinated facts | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Cross-reference correct | 0.33 ± 0.49 | 0.33 ± 0.49 | 0.33 ± 0.49 |
| **Novel inference score** | **0.62 ± 0.21** | **0.88 ± 0.21** | **0.67 ± 0.28** |

### Novel Inference by Fact Set

| Fact Set | Cond A | Cond B (EEM) | Cond C |
|----------|--------|-------------|--------|
| Software project | 50% ± 0% | **100% ± 0%** | 60% ± 14% |
| Business operations | 80% ± 11% | **100% ± 0%** | 95% ± 11% |
| Scientific experiment | 55% ± 27% | 65% ± 22% | 45% ± 27% |

### Cost and Performance

| Metric | Cond A | Cond B (EEM) | Cond C |
|--------|--------|-------------|--------|
| Mean cost (USD) | $0.34 | $2.50 | $0.40 |
| Mean duration (ms) | 52,361 | 368,202 | 58,582 |
| Mean input tokens | 311 | 610 | 353 |
| Mean output tokens | 2,639 | 16,173 | 2,861 |
| Mean cache read tokens | 271,296 | 3,371,550 | 303,657 |
| Cost ratio vs A | 1.0x | 7.4x | 1.2x |
| Duration ratio vs A | 1.0x | 7.0x | 1.1x |

## Analysis

### Finding 1: The task was too easy for the primary metric

All three conditions scored perfectly on fact recall (5/5) and correction persistence (2/2) across all 45 runs. Zero stale facts, zero hallucinations. The 5-fact, 2-correction task fits comfortably within Opus's 200K context window, and the noise injection in Condition C did not trigger actual compaction. The experiment design was correct in predicting that Condition A would score well (prediction 1), but the task was insufficiently demanding to produce the predicted degradation in Condition C (prediction 3).

This is a ceiling effect. The task needs to be harder — more facts, more corrections, longer chains of reasoning, or a model with a smaller effective context — to differentiate the conditions on correction persistence.

### Finding 2: EEM improves novel inference (+26pp)

The unexpected finding is on novel inference — questions requiring the model to combine facts in ways not explicitly stated during the task. EEM scored 88% vs conversation's 62%, a +26pp advantage.

This effect is strongest on the software project and business operations fact sets, where EEM scored 100% ± 0% on novel inference (zero variance across 5 runs). On the scientific experiment set, the advantage narrowed to 65% vs 55% — the chemistry domain may be harder to retrieve effectively.

The mechanism is likely that EEM forces explicit externalization. When the model saves each fact as a separate belief in reasons.db, it creates discrete, retrievable units. When asked a novel question, it searches reasons.db and gets clean, structured facts back — no ambiguity about what was said when. Conversation context, by contrast, holds the facts as part of a narrative that may blur boundaries between facts.

### Finding 3: EEM has zero variance on its strongest metric

On the software project and business operations fact sets, Condition B's novel inference score was 100% with zero standard deviation across all 5 runs. Conditions A and C showed variance of 0-27%. This matches prediction 4 from the experiment design: "Condition B will be more consistent across runs. Lower variance because the EEM is deterministic."

When the underlying knowledge is well-structured (discrete facts in reasons.db), retrieval is deterministic and the model's responses are correspondingly consistent. Conversation context introduces non-determinism through the model's variable attention to different parts of the accumulated context.

### Finding 4: EEM costs 7.4x more

Condition B costs $2.50 per run vs $0.34 for Condition A — a 7.4x cost multiplier. The cost comes from:

- **4 fresh sessions** (each reloading the full system prompt with CLAUDE.md): 3.37M cache read tokens vs 271K for conversation
- **Tool use overhead** in each session: `reasons add`, `reasons update`, `reasons search`, `reasons show`, plus file writes for checkpoint.md
- **Higher output token count** (16,173 vs 2,639): the model generates tool calls and their results, not just answers

The duration is 7x longer (368s vs 52s) for the same reason — each session has startup overhead and tool invocations.

This cost structure has two implications:
1. For short tasks (5 facts, 4 steps), conversation is dramatically cheaper
2. The cost crossover — where EEM becomes cheaper — would require enough conversation steps that prompt caching stops amortizing the growing context. At current pricing, that's likely 20+ steps

### Finding 5: Cross-reference scoring reveals a measurement artifact

The cross-reference score was identical across all conditions (0.33 ± 0.49) and perfectly correlated with fact set, not condition. The software project cross-reference ("who should review the session timeout PR?" → "Alice") always scored correct; the business and scientific cross-references never did.

This means the cross-reference questions for business and scientific fact sets have scoring issues — the expected answers may not match how the model phrases its response, or the questions are too ambiguous. The cross-reference metric as measured does not differentiate conditions and needs redesign.

### Finding 6: Compaction stress had no effect

Condition C is statistically indistinguishable from Condition A on all metrics. The inline noise injection (8 topic blocks × 6 repetitions of ~100 words each) added ~10% to cache read tokens (303K vs 271K) but did not trigger compaction. Opus's 200K context window handles the total load (system prompt + 4 conversation turns + noise) without compacting.

To test the compaction prediction, we need either:
- A much longer task (20+ steps with accumulated context)
- Significantly more noise (enough to push past 200K)
- A model with a smaller context window
- The upcoming LangGraph/Vertex AI variant that can inject noise at the API level

## Predictions Evaluated

| # | Prediction | Result |
|---|-----------|--------|
| 1 | Condition A will score well on recall but imperfectly on corrections | **Wrong** — scored perfectly. Task was too easy |
| 2 | Condition B will match or exceed A on corrections | **Trivially confirmed** — both perfect |
| 3 | Condition C will degrade significantly on corrections | **Wrong** — no compaction triggered |
| 4 | Condition B will be more consistent across runs | **Confirmed** — zero variance on novel inference for 2/3 fact sets |
| 5 | Condition B may score lower on novel inference initially | **Wrong** — EEM scored *higher*, not lower |
| 6 | Condition B's token cost is uncertain | **Resolved**: 7.4x more expensive than conversation |

## What This Means

The experiment answered a question we didn't design for: **does EEM improve multi-fact reasoning quality even when conversation memory is intact?** The answer is yes — +26pp on novel inference, with zero variance on the best-performing fact sets.

The experiment did not answer the designed question — does EEM preserve corrections better under compaction? — because the task was too small to trigger compaction. This isn't a negative result; it's a measurement limitation that tells us the next experiment needs to be harder.

The cost finding is important for practical deployment: EEM continuity is 7.4x more expensive per session. But per-session cost is the wrong frame for the amortization argument. If EEM's novel inference advantage compounds across a long project (where conversation would eventually compact and lose information), the total-project cost may favor EEM despite higher per-session overhead. That's the experiment we haven't run yet.

## Next Steps

1. **Redesign for harder tasks** — 15+ facts, 5+ corrections, multi-step reasoning chains, to produce differentiation on correction persistence
2. **Test with smaller context** — Sonnet or Haiku, where 200K is nominally available but compaction triggers earlier in practice
3. **Fix cross-reference scoring** — the business and scientific cross-reference questions need scoring that matches model phrasing
4. **Run LangGraph/Vertex AI variant** — API-level control over context, intelligent caching of EEM/checkpoint, lower per-call overhead
5. **Longitudinal test** — a 20+ step task spanning what would be a full work session, where compaction is inevitable

## Raw Data

Results: `~/git/claude-automated/continuity_results/results_20260519_093952.json`
Harness: `~/git/claude-automated/test_continuity_eval.py`
Fact sets: `~/git/claude-automated/continuity_fact_sets.py`
