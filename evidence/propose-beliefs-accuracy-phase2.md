# Propose-Beliefs Accuracy: Phase 2 Results

**Date:** 2026-06-09
**Source:** handbook-expert (4,496 beliefs, 3,783 IN premises), 100 sampled premises reviewed by LLM against source documents
**Related:** entries/2026/06/08/experiment-design-propose-beliefs-accuracy.md

## Results

| Metric | Value |
|--------|-------|
| Premises sampled | 100 (random from 3,783 IN premises) |
| Factually correct | 92 (92.0%) |
| Factually incorrect | 8 (8.0%) |
| Well-supported by source | 89 (89.0%) |
| ACCEPT recommendation correct | 91 (91.0%) |
| Reviewer confidence high | 88/100 |
| Reviewer confidence medium | 12/100 |

**ACCEPT precision: 92%.** This falls in the "adequate but could improve" band (85-95%) from the experiment design.

**Premise retraction rate: 8%.** Significantly lower than the 13-37% derived belief retraction rate, but not negligible.

## Error Type Distribution

| Error Type | Count | Description |
|-----------|-------|-------------|
| Misread source | 7 | Proposer fabricated specific details not in the source |
| Overgeneralized | 2 | Inferred ordering or rationale the source didn't state |
| Factually wrong | 0 | No claims that directly contradict the source |

The dominant failure mode is **fabricated specificity**. The proposer doesn't extract claims that contradict the source — it adds unsupported details to things the source does say. Examples from the flagged premises:

- **nexus-auth-refresh-tokens-in-redis:** Source describes token rotation but never mentions Redis. The proposer fabricated "stored in Redis" as a plausible implementation detail.
- **pde-team-reviews-test-type-classification:** Source says classification happens via a Slack channel. The proposer fabricated "must review and comment on JIRA" — a plausible but incorrect process.
- **nexus-approval-http-not-message-queues:** Source confirms HTTP-based communication with different rationale than claimed, and introduces PostgreSQL NOTIFY and Redis Streams as contrasts that appear nowhere in the source.
- **eda-tick-plugin-removed-replaced-by-generic-range:** Source confirms tick removal but doesn't name the replacement. Proposer fabricated "generic range source plugins."

This is the "coherence isn't correctness" limitation applied to the front gate. These fabrications are plausible, internally consistent, and pass every coherence check. They fail only when verified against the actual source material.

## Comparison to Derived Belief Retraction Rate

| Stage | Retraction Rate | Error Type |
|-------|----------------|------------|
| Propose (premises) | 8% | Fabricated specificity, overgeneralization |
| Derive (derived beliefs) | 13-37% | Invalid reasoning, insufficient evidence, unnecessary conclusions |

The 8% premise error rate is about half the low end of the derive range. This confirms the hypothesis: **premises are higher quality than derived beliefs, but the proposer gate is not as reliable as assumed.**

The difference in error types matters. Derive errors are reasoning failures (bad logic connecting correct premises). Propose errors are grounding failures (plausible details not in the source). Derive errors are caught by `review-beliefs` checking logical validity. Propose errors are not caught by any existing automated step — they require source verification.

## Propagation Risk

The 8% false premise rate has compounding effects. Each false premise that enters the network can:

1. Serve as an antecedent for derived beliefs that pass review (valid reasoning from a false premise produces a false conclusion)
2. Avoid detection by `review-beliefs` (which checks logical validity, not factual accuracy)
3. Accumulate over time — at 8% per round, after 5 rounds of proposition from new sources, roughly 34% of premises contain at least one fabricated detail

For handbook-expert with 3,783 premises, 8% means approximately **303 premises contain fabricated details.** Most of these are embellishments of correct claims (wrong mechanism, wrong technology, wrong rationale) rather than entirely wrong claims. But they corrupt the precision of the knowledge base.

## Implications

### What the 8% means for the pipeline

The dirty pipeline math applies in reverse here. If 8% of premises are wrong and some fraction of derived beliefs depend on them, the network contains a layer of plausible-but-wrong knowledge that no downstream step can catch. The review step evaluates "does the conclusion follow from the premises?" — and yes, it does follow. The premises are just wrong.

This is exactly the problem described in the experiment design: "A valid derivation from a false premise produces a false conclusion that passes review."

### What to do about it

From the experiment design's response catalog:

1. **Add adversarial review to proposals** — run a second LLM pass that specifically challenges proposed beliefs against the source material. This is the most direct fix. Cost: roughly doubles the propose step.

2. **Source verification** — for each proposed belief, query the source with "does this document actually say [claim]?" Catches the fabricated-specificity error type directly.

3. **Better prompting** — the current prompt says "well-supported by source material." Adding "do not infer implementation details not explicitly stated in the source" could reduce fabricated specificity.

4. **Review-beliefs on premises** — the current tool skips premises because they have no justifications to evaluate. Adding a premise-review mode that checks claims against source text would close this gap. This is the highest-leverage tooling improvement.

Option 4 is the structural fix. The others are patches. If `review-beliefs` could evaluate premises against their source material (not just derived beliefs against their antecedents), the same derive-then-review architecture would apply to the front gate.

## Process

### Why not `review-beliefs`?

The experiment design called for running `review-beliefs` on premises. This failed: `review-beliefs` filters for derived beliefs (nodes with justifications) and skips premises entirely. Line 2541-2546 of `ftl-reasons/reasons_lib/api.py` builds `all_derived` by requiring `len(v["justifications"]) > 0`. Even when specific IDs are passed as arguments, they're filtered against this derived-only set. The tool returned "No derived beliefs to review."

This is architecturally correct — `review-beliefs` evaluates whether a conclusion follows from its antecedents. Premises have no antecedents. The evaluation question for premises is different: "does the source material actually say this?"

### Custom evaluation script

Wrote `/tmp/review-premises.py` to fill the gap:

1. **Export network** from handbook-expert's `reasons.db` via `reasons_lib.api.export_network()`
2. **Filter** for IN premises: `truth_value == "IN"` and no justifications (depth 0)
3. **Sample** 100 premises using the pre-generated random sample (`/tmp/premise-sample-ids.txt`, seed 42)
4. **For each batch of 5 premises:**
   - Load the source document referenced in the belief's `source` field (e.g., `entries/2026/06/08/ANSTRAT-1899-automation-orchestrator.md`)
   - Truncate source to first 3,000 characters
   - Send the premise text + source content to an LLM (Claude via `reasons_lib.llm.invoke_model`)
   - Ask the LLM to evaluate: factually correct? well-supported? ACCEPT recommendation correct? error type? confidence? reasoning?
   - Parse the JSON response
5. **Aggregate** across all 100 reviews: compute precision, support rate, error type distribution, confidence distribution

### The evaluation prompt

The LLM was asked to evaluate each premise on six dimensions:

- `factually_correct` — does the claim match the source material? (boolean)
- `well_supported` — is the claim well-supported, not vague or overgeneralized? (boolean)
- `accept_correct` — was the ACCEPT recommendation correct? (boolean)
- `error_type` — classification if wrong: `false_accept_factually_wrong`, `false_accept_misread_source`, `false_accept_overgeneralized`, `false_accept_conflated`, `none`
- `confidence` — reviewer's confidence in the judgment (high/medium/low)
- `reasoning` — 1-2 sentence explanation

### Limitations

- **The reviewer is another LLM call.** These results have their own accuracy ceiling — the reviewer may miss errors or flag correct beliefs. Phase 1 (human-judged sample) would provide ground truth.
- **Source truncation at 3,000 characters.** For long source documents, the reviewer may not see the section that supports (or contradicts) the belief. This could produce both false positives and false negatives.
- **Same model reviewing its own generation.** The proposer and reviewer are both Claude. A cross-model review (e.g., Gemini reviewing Claude's proposals) might catch different errors.
- **Single pass.** Each premise was reviewed once. Multiple reviewers or multiple passes could improve reliability.

## Connection to Prior Work

This result validates the experiment design's hypothesis: "Premise retraction rate should be significantly lower than derived belief retraction rate." It is lower (8% vs 13-37%). But the design also predicted that if the rate exceeds 5%, "review-beliefs on premises would help." At 8%, that recommendation applies.

The error type distribution — dominated by fabricated specificity rather than factual contradiction — is a new finding. It suggests that the proposer's failure mode is not "the model doesn't know" but "the model adds what it thinks should be there." This is the generation-vs-review gap applied to knowledge extraction: the model generates plausible details during proposition that it would flag during adversarial review.
