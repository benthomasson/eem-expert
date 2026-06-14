# Evidence

Methodology entries and experimental results backing the claims made on [llmeem.ai](https://llmeem.ai). Each file contains the experimental design, procedure, raw numbers, and analysis for a specific evaluation.

## Claim → Evidence Map

| Claim | Evidence File | Key Numbers |
|-------|--------------|-------------|
| 98.5% A/B across 3,853 questions | [full-scale-validation-3853-questions.md](full-scale-validation-3853-questions.md) | 2549 A + 1246 B + 58 C, zero D/F. Opus, dual-path architecture |
| 88% vs 33% expert-vs-baseline | [three-way-eval-88-vs-33.md](three-way-eval-88-vs-33.md) | 50 questions, 5 models tested. Expert-service 88% A (Opus) vs agents-python 33% A |
| 0.53x cost, +12.7pp recall | [eem-vs-scratch-eval.md](eem-vs-scratch-eval.md) | 55 questions (40 MC + 15 OE). AAP domain. EEM $7.25 vs from-scratch $13.61 |
| Beliefs +12-14pp on architectural questions | [architectural-ablation-results.md](architectural-ablation-results.md) | 2,100 invocations. 4 models × 3 conditions × 5 runs × 35 questions |
| Confidence r=0.14-0.28, revision damages accuracy | [confidence-experiment-results.md](confidence-experiment-results.md) | 4 models. Revision: -3pp (Opus) to -41.5pp (Pro) |
| Confidence experiment methodology | [confidence-experiment-design.md](confidence-experiment-design.md) | 3 conditions × 5 runs × 55 questions. No-tools baseline |
| 92% premise precision, 8% fabricated specificity | [propose-beliefs-accuracy-phase2.md](propose-beliefs-accuracy-phase2.md) | 100 sampled premises from 3,783. Custom eval script |
| +26pp novel inference with EEM | [continuity-experiment-results.md](continuity-experiment-results.md) | 45 runs, 3 conditions. EEM 88% vs conversation 62% |

## Related Public Repositories

- **[expert-service](https://github.com/benthomasson/expert-service)** — `eval/` directory contains question sets (`questions.json`, `open_ended.json`), scoring code (`scoring.py`), eval harness (`run_eval.py`), and raw result JSONs
- **[ftl-reasons](https://github.com/benthomasson/ftl-reasons)** — the EEM engine (TMS implementation)
- **[expert-agent-builder](https://github.com/benthomasson/expert-agent-builder)** — automated pipeline from sources to belief network

## Raw Data

See the [`data/`](../data/) directory for question sets, analysis summaries, and experiment scripts. Full per-run result files (60-200+ JSON files per experiment) are available on request.

## Models and Dates

All experiments run between February–June 2026 using:
- **Anthropic:** Claude 3.5 Sonnet (`claude-sonnet-4-20250514`), Claude 3.5 Opus (`claude-opus-4-20250514`), Claude 3.5 Haiku via Vertex AI (us-east5)
- **Google:** Gemini 2.5 Flash, Gemini 2.5 Pro via Vertex AI (global)
- **Local:** Gemma4 27B, Qwen3 14B/27B via Ollama

Model versions matter — results may differ on newer versions.
