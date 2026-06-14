---
schema_version: "1.0"
type: eem
project_name: eem-expert
domain:
  - external-epistemic-memory
  - truth-maintenance-systems
  - llm-knowledge-management
license: mit
base_network: null
source_repos:
  - benthomasson/ftl-reasons
beliefs_total: 49
beliefs_in: 49
beliefs_out: 0
premises: 19
derived: 30
nogoods: 0
generator: ftl-reasons/0.40.0
---

# EEM Expert

Expert knowledge base for explaining External Epistemic Memory (EEM) to humans and LLM-based agents. Contains 49 justified beliefs covering what EEM is, how it works, why it matters, and empirical evidence for its effectiveness.

## What is this?

This is an **External Epistemic Memory** (EEM) — a model-agnostic knowledge base that any LLM can use via the `reasons` CLI or tool calling. Unlike a LoRA or fine-tune, this knowledge is not baked into model weights. It is external, inspectable, correctable, and works with any model.

## Stats

| Metric | Value |
|--------|-------|
| Total beliefs | 49 |
| Status | 49 IN / 0 OUT |
| Premises (observations) | 19 |
| Derived (justified conclusions) | 30 |
| Nogoods (contradictions) | 0 |
| Retraction rate | 0% |
| Max derivation depth | 3 |

## Domain Coverage

- **What EEM is**: three load-bearing properties (external, epistemic, memory), formal definition
- **How EEM differs from alternatives**: vs RAG, vs context/conversation history, vs parametric knowledge
- **TMS architecture**: Doyle 1979 foundations, SL justifications, retraction cascades, nogoods, backtracking
- **Empirical evidence**: ablation studies, dual-path validation, confidence unreliability, model compensation
- **Design principles**: derive-then-review, cognitive budget, wide-not-deep, generate-and-critique
- **Practical workflows**: expert pipeline, how agents use EEM, how humans use EEM, multi-agent belief tracking

## How to Use

### Import into a reasons database

```bash
reasons init
reasons import-json network.json
```

### Query beliefs

```bash
reasons search "what is EEM"
reasons explain eem-definition
reasons show eem-three-properties
```

### Use as an MCP tool or CLI

Any LLM agent that can call `reasons search`, `reasons show`, and `reasons explain` can use this knowledge base. The agent does not need to be told it is an expert — the knowledge base speaks for itself (see belief `expert-prompt-paradox`).

## Key Beliefs

| Node | Summary |
|------|---------|
| `eem-definition` | EEM is knowledge that lives outside the model, carries its justifications, and lets you understand how the system knows what it knows |
| `eem-three-properties` | External, epistemic, memory — three load-bearing properties |
| `eem-works` | EEM measurably and dramatically improves LLM performance on domain tasks |
| `evidence-dual-path` | Opus + dual-path achieves 98.5% A/B across 3,853 questions |
| `evidence-retraction-rate` | 13-37% of derived beliefs retracted per review round — self-correction works |
| `confidence-unreliable` | LLM self-assessed confidence does not track accuracy (r=-0.182 to r=0.219) |
| `ftl-reasons-is-tms` | ftl-reasons implements Doyle-style TMS with LLMs as problem solvers |

## Evidence

All performance claims are backed by methodology writeups and raw data in this repository:

| Claim | Evidence | Data |
|-------|----------|------|
| 98.5% A/B across 3,853 questions | [evidence/full-scale-validation-3853-questions.md](evidence/full-scale-validation-3853-questions.md) | — |
| 88% vs 33% expert-vs-baseline | [evidence/three-way-eval-88-vs-33.md](evidence/three-way-eval-88-vs-33.md) | — |
| 0.53x cost, +12.7pp recall | [evidence/eem-vs-scratch-eval.md](evidence/eem-vs-scratch-eval.md) | — |
| Beliefs +12-14pp on architectural Qs | [evidence/architectural-ablation-results.md](evidence/architectural-ablation-results.md) | [questions](data/architectural-ablation-questions.json), [analysis](data/architectural-ablation-analysis.json) |
| Confidence unreliable (r=0.14-0.28) | [evidence/confidence-experiment-results.md](evidence/confidence-experiment-results.md) | [analysis](data/confidence-analysis.json), [harness](data/confidence-run-experiment.py) |
| 92% premise precision | [evidence/propose-beliefs-accuracy-phase2.md](evidence/propose-beliefs-accuracy-phase2.md) | — |
| +26pp novel inference | [evidence/continuity-experiment-results.md](evidence/continuity-experiment-results.md) | — |

See [evidence/README.md](evidence/README.md) for the full claim-to-evidence map and [data/README.md](data/README.md) for raw data files.

Additional evaluation infrastructure (question sets, scoring code, eval harness, raw results) is publicly available in [expert-service/eval/](https://github.com/benthomasson/expert-service/tree/main/eval).

## Sources

Built from exploration of [benthomasson/ftl-reasons](https://github.com/benthomasson/ftl-reasons) and empirical studies across 40+ expert knowledge bases ranging from 237 to 12,731 beliefs.

## Files

| File | Description |
|------|-------------|
| `network.json` | Full belief network (machine-readable, portable) |
| `reasons.db` | SQLite database (gitignored, regenerate with `reasons import-json network.json`) |
| `CLAUDE.md` | Agent instructions for using this knowledge base |

## Quality

- All 49 beliefs are IN (none retracted)
- 19 premises grounded in direct observations and published research
- 30 derived beliefs justified from premises via SL justifications
- 0 nogoods — no contradictions detected
- Built and reviewed using ftl-reasons derive and review-beliefs pipeline

## Limitations

- Focused on EEM concepts and ftl-reasons implementation — does not cover alternative TMS implementations in detail
- Empirical evidence drawn primarily from code-expert use cases
- No ATMS or assumption-based beliefs (single-context TMS only)
- PostgreSQL multi-tenant patterns not covered

## Authors

- **Ben Thomasson** ([@benthomasson](https://github.com/benthomasson)) — Senior Principal Software Engineer, Red Hat. Research on external epistemic memory for LLM agents.

## License

mit
