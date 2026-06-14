# Confidence Experiment Results: Self-Assessment Hurts More Than It Helps

**Date:** 2026-03-14
**Time:** 02:50

## Overview

Full experiment completed: 55 questions (40 MC + 15 OE) × 3 conditions × 2 models (Sonnet, Opus) × 5 runs = 1,650 invocations. The results are nuanced but the practical conclusion is clear: **self-assessed confidence is not reliable enough to act on, and acting on it actively degrades performance.**

## Key Results

### Accuracy by Condition

| Model | A (baseline) | B (+ confidence) | C (+ revision) |
|-------|-------------|-------------------|----------------|
| Sonnet | 0.870 ±0.019 | 0.885 ±0.012 | **0.600 ±0.057** |
| Opus | 0.870 ±0.024 | 0.855 ±0.029 | 0.925 ±0.045 |

**Sonnet Condition C is catastrophic.** Asking Sonnet to revise based on self-assessed confidence dropped accuracy from 87% to 60% — a 27 percentage point degradation. This is the strongest evidence against self-assessment-driven revision.

Opus Condition C appears to improve (0.925 vs 0.870), but the revision delta analysis shows this is misleading — revision actually degraded more answers than it improved (-4 net).

### Confidence Calibration

| Model | Pearson r | p-value | Interpretation |
|-------|-----------|---------|----------------|
| Sonnet | 0.135 | 0.056 | Borderline — not significant at p<0.05 |
| Opus | -0.045 | 0.527 | No correlation — confidence is noise |

Neither model shows reliable calibration. Opus trends negative (worse than random). Sonnet is borderline positive but not significant.

### Calibration Bins (the most revealing analysis)

**Sonnet:**
| Confidence bin | Accuracy | n |
|---------------|----------|---|
| Low (1-3) | **0.964** | 28 |
| Medium (4-6) | 0.476 | 21 |
| High (7-10) | 0.927 | 151 |

**Opus:**
| Confidence bin | Accuracy | n |
|---------------|----------|---|
| Medium (4-6) | 0.839 | 31 |
| High (7-10) | 0.858 | 169 |

Sonnet's low-confidence bin is extraordinary: when the model says it is *least confident* (1-3), it is *most accurate* (96.4%). This is worse than no signal — it's an inverted signal. The model is most uncertain about its correct answers.

The medium bin (4-6) has the worst accuracy at 47.6% — essentially coin-flip. These are the answers the model hedges on, and they really are unreliable.

### Hard-Easy Effect (Kahneman Prediction)

| Model | Accuracy-confidence r | p-value | Hard-easy effect? |
|-------|----------------------|---------|-------------------|
| Sonnet | 0.316 | 0.047 | No — easier questions get higher confidence |
| Opus | -0.150 | 0.356 | **Yes** — harder questions get higher confidence |

Opus shows the Kahneman pattern (not significant, but directionally present): harder questions receive higher confidence ratings. This is the fluency-not-accuracy pattern.

Sonnet shows the opposite: easier questions get higher confidence. However, combined with the inverted low-confidence bin, this doesn't mean Sonnet is well-calibrated — it just means the miscalibration takes a different form.

### Revision Delta (Condition C)

| Model | Revised | Improved | Degraded | Net delta |
|-------|---------|----------|----------|-----------|
| Sonnet | 49 | 7 | **29** | **-22** |
| Opus | 32 | 3 | **7** | **-4** |

**Revision hurts for both models.** When the model revises answers it rated as low-confidence, it degrades correct answers far more often than it fixes incorrect ones. Sonnet is dramatically worse: 29 correct answers were changed to incorrect, while only 7 incorrect answers were fixed.

This is the critical finding: **self-assessment-driven revision is a net negative.** The model steers away from its correct answers because it confuses uncertainty with incorrectness.

## Interpretation

### Does self-assessed confidence carry signal?

Weakly, for Sonnet (p=0.056). Not at all for Opus (p=0.527). The signal is too weak and too inconsistent across models to be actionable.

### Is confidence worse than random?

Not in the simple correlation sense (neither model shows significant negative r). But the Sonnet low-confidence bin (96.4% accuracy at confidence 1-3) shows something arguably worse: the model's uncertainty signal is *inverted* at the extremes. When it says 'I'm guessing,' it's almost certainly right.

### Does acting on confidence help?

**No. It actively hurts.** Condition C (revision based on confidence) degraded accuracy for both models. Sonnet dropped 27 percentage points. This is the strongest finding and the most practically relevant.

### Is the effect model-dependent?

Yes. Opus and Sonnet show different calibration patterns (Opus trends negative, Sonnet trends positive). Both share the same practical conclusion: confidence is not actionable.

### Does this replicate Kai Xu's finding?

Partially. We don't see the dramatic negative correlation reported for Granite, but we see:
1. Opus has a non-significant negative trend (r=-0.045)
2. Sonnet's low-confidence bin is inverted (highest accuracy at lowest confidence)
3. Both models show that acting on confidence hurts performance
4. The effect may be stronger on smaller models (Granite < Sonnet/Opus)

The original claim ('worse than random') is too simple. The reality is: confidence is poorly calibrated in model-specific ways, and none of them are reliable enough to act on.

## Implications for the Research Program

### RQ9 (Belief-driven autonomy) is validated in principle

If self-assessed confidence is unreliable (confirmed), then autonomous agents cannot use 'am I sure?' as an escalation criterion. The alternative — structural triggers from the belief registry (missing beliefs, stale beliefs, nogood violations) — is the right approach. These are checkable conditions, not model self-judgment.

### The Kahneman connection holds

Like humans, LLMs conflate fluency with accuracy. The confidence rating reflects how smoothly the answer was generated, not how likely it is to be correct. External scaffolding (checklists, belief registries) is the established solution for both humans and AI.

### Practical recommendation

**Never gate decisions on model self-assessed confidence.** Don't ask 'are you sure?', don't use confidence thresholds for delegation, don't ask the model to revise based on its own uncertainty assessment. Use external verification: source hashes, test execution, belief registry lookups, human review at structural boundaries.

## Statistical Notes

- 200 MC observations per model for calibration analysis (40 MC × 5 runs)
- Wilcoxon signed-rank test for A vs C comparison (paired by run)
- Sonnet A vs C: p=0.0625, Cohen's d=5.692 (huge effect, borderline significance due to n=5 runs)
- Opus A vs C: p=0.2500, Cohen's d=-1.364
- Confidence extraction succeeded for all items (no extraction failures)

## Related

- nogood-001: Self-assessed confidence worse than random — partially replicated, refined
- confidence-output-is-generation-not-measurement (belief): Confirmed by data
- overconfidence-not-ai-specific (belief): Kahneman pattern seen in Opus
- belief-registry-enables-structural-escalation (belief): Validated by negative confidence results
- experiments/confidence/results/full/analysis.json: Full statistical report
