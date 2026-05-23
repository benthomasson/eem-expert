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

- Ben Thomasson ([@benthomasson](https://github.com/benthomasson))

## License

mit
