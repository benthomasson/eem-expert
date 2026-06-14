# Raw Data

Question sets, analysis summaries, and experiment scripts for independent verification of EEM claims.

## Files

### Architectural Ablation Experiment

- **[architectural-ablation-questions.json](architectural-ablation-questions.json)** — 35 questions: 20 architectural MC, 5 architectural OE, 10 factual controls. Used to test whether beliefs help more on multi-file architectural reasoning than single-file factual lookup.
- **[architectural-ablation-analysis.json](architectural-ablation-analysis.json)** — Aggregate results across 4 models × 3 conditions × 5 runs (60 individual run files). Includes per-model, per-condition, per-question-type breakdowns.

### Confidence Experiment

- **[confidence-analysis.json](confidence-analysis.json)** — Correlation analysis across 4 models (Opus, Sonnet, Gemini Pro, Gemini Flash). r-values, revision deltas, per-confidence-bin accuracy.
- **[confidence-run-experiment.py](confidence-run-experiment.py)** — Experiment harness. Defines 3 conditions: A (no confidence), B (post-hoc rating), C (gated revision). 55 questions × 5 runs per condition.
- **[confidence-score-results.py](confidence-score-results.py)** — Scoring script. MC exact-match, OE key-fact extraction, confidence correlation computation.

### Expert-Service Evaluation (Public Repository)

The following are in [expert-service/eval/](https://github.com/benthomasson/expert-service/tree/main/eval):
- `questions.json` — 40 MC questions (AAP domain)
- `open_ended.json` — 15 OE questions with key-fact rubrics
- `scoring.py` — MC exact-match + LLM-as-judge scoring
- `run_eval.py` — Evaluation harness
- `results/` — Raw result JSONs from evaluation runs

## Full Per-Run Data

Each experiment produced 60-200+ individual JSON result files (one per model × condition × run). These are not included here to keep the repository navigable. They are available on request — file an issue or contact the author.

## Reproducing Experiments

The experiment scripts define the full methodology:
1. Question sets define what was asked
2. Conditions define what context was provided (no beliefs, with beliefs, with code, etc.)
3. Scoring scripts define how answers were graded
4. Analysis scripts compute aggregate statistics

To reproduce: run the experiment script against the same model versions with the same question sets. Results will vary with model version updates.
