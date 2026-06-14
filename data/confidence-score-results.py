"""
Score and analyze results from the confidence experiment.

Reads result JSON files, scores MC (exact match) and OE (LLM-as-judge),
then produces:
  1. Per-condition accuracy summaries
  2. Confidence calibration analysis (correlation with correctness)
  3. Hard-easy effect test (Kahneman prediction)
  4. Revision delta analysis (Condition C)
  5. Statistical tests (paired Wilcoxon, Cohen's d)

Usage:
  python score_results.py [--results-dir results/]
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats


def extract_answer(response: str) -> str:
    """Extract MC answer letter from LLM response.

    Handles formats like:
    - "ANSWER: b"
    - "The correct answer is **a)..."
    - "The answer is **b) Receptor**"
    - "**b**"
    - A bare letter on its own line
    """
    if not response:
        return ""

    # 1. Look for ANSWER: line
    m = re.search(r"ANSWER:\s*\**([a-d])\**", response, re.IGNORECASE)
    if m:
        return m.group(1).lower()

    # 2. "The correct answer is **a)" or "The answer is **b)"
    m = re.search(
        r"(?:correct |right )?answer is[:\s]*\**([a-d])\)*",
        response, re.IGNORECASE,
    )
    if m:
        return m.group(1).lower()

    # 3. "I confirm my original answer: **b)"
    m = re.search(r"answer[:\s]*\**([a-d])\)*", response, re.IGNORECASE)
    if m:
        return m.group(1).lower()

    # 4. Standalone bolded letter: **b** or **b)
    m = re.search(r"\*\*([a-d])\*\*", response)
    if m:
        return m.group(1).lower()

    # 5. Bolded letter with closing paren: **b) ... (Opus style, often at start)
    m = re.search(r"\*\*([a-d])\)", response)
    if m:
        return m.group(1).lower()

    # 6. Fallback: single letter on its own line
    for line in reversed(response.strip().split("\n")):
        line = re.sub(r"[*_`]", "", line).strip()
        if re.match(r"^[a-d]$", line, re.IGNORECASE):
            return line.lower()

    return response.strip()[:100]


def load_results(results_dir):
    """Load all result files, grouped by model and condition."""
    results = defaultdict(lambda: defaultdict(list))
    for f in sorted(Path(results_dir).glob("*.json")):
        parts = f.stem.split("_")  # e.g. sonnet_B_run1
        if len(parts) < 3:
            continue
        model = parts[0]
        condition = parts[1]
        data = json.load(open(f))
        results[model][condition].append(data)
    return results


def score_mc_results(run_data):
    """Score MC questions in a single run. Returns list of (question_id, correct, confidence)."""
    scored = []
    for item in run_data:
        if item["question_type"] != "mc":
            continue
        # Use the final response (revised_response if condition C and revised)
        response = item.get("revised_response") or item["response"]
        if not response:
            scored.append((item["question_id"], False, item.get("confidence")))
            continue
        extracted = extract_answer(response)
        correct = extracted == item["correct_answer"].strip().lower()
        scored.append((item["question_id"], correct, item.get("confidence")))
    return scored


def analyze_calibration(all_scored):
    """Analyze confidence calibration across all scored results.

    all_scored: list of (question_id, correct: bool, confidence: int|None)
    Returns dict with calibration metrics.
    """
    # Filter to items with confidence ratings
    with_conf = [(qid, c, conf) for qid, c, conf in all_scored if conf is not None]

    if not with_conf:
        return {"n": 0, "error": "no confidence ratings found"}

    correctness = np.array([1 if c else 0 for _, c, _ in with_conf])
    confidence = np.array([conf for _, _, conf in with_conf])

    # Pearson correlation
    if len(set(confidence)) < 2 or len(set(correctness)) < 2:
        pearson_r, pearson_p = 0.0, 1.0
        spearman_r, spearman_p = 0.0, 1.0
    else:
        pearson_r, pearson_p = stats.pearsonr(confidence, correctness)
        spearman_r, spearman_p = stats.spearmanr(confidence, correctness)

    # Calibration bins
    bins = {"low (1-3)": [], "medium (4-6)": [], "high (7-10)": []}
    for _, correct, conf in with_conf:
        if conf <= 3:
            bins["low (1-3)"].append(correct)
        elif conf <= 6:
            bins["medium (4-6)"].append(correct)
        else:
            bins["high (7-10)"].append(correct)

    bin_accuracy = {}
    for label, items in bins.items():
        if items:
            bin_accuracy[label] = {
                "n": len(items),
                "accuracy": sum(items) / len(items),
            }
        else:
            bin_accuracy[label] = {"n": 0, "accuracy": None}

    return {
        "n": len(with_conf),
        "mean_confidence": float(np.mean(confidence)),
        "mean_accuracy": float(np.mean(correctness)),
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_r": float(spearman_r),
        "spearman_p": float(spearman_p),
        "calibration_bins": bin_accuracy,
        "confidence_distribution": {
            str(i): int(np.sum(confidence == i)) for i in range(1, 11)
        },
    }


def analyze_hard_easy_effect(all_scored):
    """Test Kahneman's hard-easy effect: are harder questions given higher confidence?

    Groups questions by baseline difficulty, checks if confidence is inversely
    correlated with accuracy (the Kahneman prediction).
    """
    # Group by question to get per-question accuracy
    question_stats = defaultdict(lambda: {"correct": 0, "total": 0, "confidences": []})
    for qid, correct, conf in all_scored:
        question_stats[qid]["correct"] += int(correct)
        question_stats[qid]["total"] += 1
        if conf is not None:
            question_stats[qid]["confidences"].append(conf)

    # Need questions with both accuracy data and confidence ratings
    questions_with_both = []
    for qid, s in question_stats.items():
        if s["total"] > 0 and s["confidences"]:
            acc = s["correct"] / s["total"]
            mean_conf = np.mean(s["confidences"])
            questions_with_both.append((qid, acc, mean_conf))

    if len(questions_with_both) < 3:
        return {"error": "too few questions with both accuracy and confidence data"}

    accuracies = np.array([a for _, a, _ in questions_with_both])
    confidences = np.array([c for _, _, c in questions_with_both])

    if len(set(accuracies)) < 2 or len(set(confidences)) < 2:
        return {"error": "insufficient variance in accuracy or confidence"}

    r, p = stats.spearmanr(accuracies, confidences)

    # Classify questions as easy (acc >= 0.8) vs hard (acc < 0.5)
    easy = [c for _, a, c in questions_with_both if a >= 0.8]
    hard = [c for _, a, c in questions_with_both if a < 0.5]

    return {
        "n_questions": len(questions_with_both),
        "accuracy_confidence_correlation": float(r),
        "p_value": float(p),
        "hard_easy_effect": r < 0,  # True = Kahneman effect present
        "easy_questions_mean_confidence": float(np.mean(easy)) if easy else None,
        "hard_questions_mean_confidence": float(np.mean(hard)) if hard else None,
        "easy_n": len(easy),
        "hard_n": len(hard),
    }


def analyze_revision_delta(results_c):
    """Analyze whether confidence-gated revision helps or hurts (Condition C).

    Compares original vs revised answers for items where revision occurred.
    """
    improved = 0
    degraded = 0
    unchanged = 0
    total_revised = 0
    total_confirmed = 0

    for run in results_c:
        for item in run:
            if item["question_type"] != "mc":
                continue
            if not item.get("revised"):
                total_confirmed += 1
                continue

            total_revised += 1
            correct_answer = item["correct_answer"].strip().lower()
            original = extract_answer(item["response"] or "")
            revised = extract_answer(item["revised_response"] or "")

            orig_correct = original == correct_answer
            rev_correct = revised == correct_answer

            if not orig_correct and rev_correct:
                improved += 1
            elif orig_correct and not rev_correct:
                degraded += 1
            else:
                unchanged += 1

    return {
        "total_revised": total_revised,
        "total_confirmed": total_confirmed,
        "improved": improved,
        "degraded": degraded,
        "unchanged": unchanged,
        "net_delta": improved - degraded,
        "revision_helps": improved > degraded,
    }


def cohens_d(group1, group2):
    """Calculate Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return None
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((mean1 - mean2) / pooled_std)


def compare_conditions(results, model):
    """Compare accuracy across conditions A, B, C for a given model."""
    condition_accuracies = {}

    for condition in ["A", "B", "C"]:
        if condition not in results[model]:
            continue
        runs = results[model][condition]
        run_accuracies = []
        for run in runs:
            scored = score_mc_results(run)
            if scored:
                acc = sum(1 for _, c, _ in scored if c) / len(scored)
                run_accuracies.append(acc)
        condition_accuracies[condition] = run_accuracies

    comparisons = {}

    # A vs C: does revision help or hurt?
    if "A" in condition_accuracies and "C" in condition_accuracies:
        a = condition_accuracies["A"]
        c = condition_accuracies["C"]
        if len(a) >= 2 and len(c) >= 2:
            if len(a) == len(c):
                stat, p = stats.wilcoxon(a, c)
            else:
                stat, p = stats.mannwhitneyu(a, c, alternative="two-sided")
            comparisons["A_vs_C"] = {
                "A_mean": float(np.mean(a)),
                "C_mean": float(np.mean(c)),
                "statistic": float(stat),
                "p_value": float(p),
                "cohens_d": cohens_d(a, c),
                "revision_helps": float(np.mean(c)) > float(np.mean(a)),
            }

    return {
        "accuracies": {k: {"mean": float(np.mean(v)), "std": float(np.std(v)),
                           "runs": v}
                       for k, v in condition_accuracies.items()},
        "comparisons": comparisons,
    }


def generate_report(results, output_path=None):
    """Generate the full analysis report."""
    report = {
        "experiment": "Self-Assessed Confidence vs Random (nogood-001)",
        "models": {},
    }

    for model in sorted(results.keys()):
        print(f"\n{'='*60}")
        print(f"Model: {model}")
        print(f"{'='*60}")

        model_report = {}

        # 1. Per-condition accuracy
        print("\n--- Accuracy by Condition ---")
        comparison = compare_conditions(results, model)
        model_report["accuracy"] = comparison
        for cond, acc in comparison["accuracies"].items():
            print(f"  Condition {cond}: {acc['mean']:.3f} "
                  f"(±{acc['std']:.3f}, n={len(acc['runs'])})")
        for comp_name, comp in comparison["comparisons"].items():
            print(f"  {comp_name}: p={comp['p_value']:.4f}, "
                  f"d={comp['cohens_d']:.3f}" if comp['cohens_d'] else "")

        # 2. Calibration analysis (Condition B)
        if "B" in results[model]:
            print("\n--- Confidence Calibration (Condition B) ---")
            all_scored_b = []
            for run in results[model]["B"]:
                all_scored_b.extend(score_mc_results(run))
            calibration = analyze_calibration(all_scored_b)
            model_report["calibration"] = calibration

            if "error" not in calibration:
                print(f"  n = {calibration['n']}")
                print(f"  Mean confidence: {calibration['mean_confidence']:.2f}")
                print(f"  Mean accuracy:   {calibration['mean_accuracy']:.3f}")
                print(f"  Pearson r:  {calibration['pearson_r']:.3f} "
                      f"(p={calibration['pearson_p']:.4f})")
                print(f"  Spearman r: {calibration['spearman_r']:.3f} "
                      f"(p={calibration['spearman_p']:.4f})")
                if calibration['pearson_r'] < 0:
                    print(f"  ** WORSE THAN RANDOM (negative correlation) **")
                elif calibration['pearson_p'] > 0.05:
                    print(f"  ** NO SIGNIFICANT CORRELATION (p > 0.05) **")
                else:
                    print(f"  ** POSITIVE CORRELATION (confidence carries signal) **")

                print(f"  Calibration bins:")
                for label, data in calibration["calibration_bins"].items():
                    if data["accuracy"] is not None:
                        print(f"    {label}: {data['accuracy']:.3f} (n={data['n']})")

        # 3. Hard-easy effect
        if "B" in results[model]:
            print("\n--- Hard-Easy Effect (Kahneman) ---")
            # Combine A and B results to get difficulty estimates
            all_scored = []
            for cond in ["A", "B"]:
                if cond in results[model]:
                    for run in results[model][cond]:
                        all_scored.extend(score_mc_results(run))
            hard_easy = analyze_hard_easy_effect(all_scored)
            model_report["hard_easy"] = hard_easy

            if "error" not in hard_easy:
                print(f"  Accuracy-confidence correlation: "
                      f"r={hard_easy['accuracy_confidence_correlation']:.3f} "
                      f"(p={hard_easy['p_value']:.4f})")
                if hard_easy["hard_easy_effect"]:
                    print(f"  ** HARD-EASY EFFECT PRESENT "
                          f"(harder questions get higher confidence) **")
                else:
                    print(f"  No hard-easy effect detected")
                if hard_easy["easy_questions_mean_confidence"] is not None:
                    print(f"  Easy questions mean confidence: "
                          f"{hard_easy['easy_questions_mean_confidence']:.2f} "
                          f"(n={hard_easy['easy_n']})")
                if hard_easy["hard_questions_mean_confidence"] is not None:
                    print(f"  Hard questions mean confidence: "
                          f"{hard_easy['hard_questions_mean_confidence']:.2f} "
                          f"(n={hard_easy['hard_n']})")

        # 4. Revision delta (Condition C)
        if "C" in results[model]:
            print("\n--- Revision Delta (Condition C) ---")
            revision = analyze_revision_delta(results[model]["C"])
            model_report["revision_delta"] = revision

            print(f"  Total revised (confidence < 7): {revision['total_revised']}")
            print(f"  Total confirmed (confidence >= 7): {revision['total_confirmed']}")
            if revision['total_revised'] > 0:
                print(f"  Improved:  {revision['improved']}")
                print(f"  Degraded:  {revision['degraded']}")
                print(f"  Unchanged: {revision['unchanged']}")
                print(f"  Net delta: {revision['net_delta']}")
                if revision['revision_helps']:
                    print(f"  ** REVISION HELPS (net positive) **")
                else:
                    print(f"  ** REVISION HURTS (net negative or zero) **")

        report["models"][model] = model_report

    # Save report
    if output_path:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nFull report saved to {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Score confidence experiment results")
    parser.add_argument("--results-dir",
                        default=str(Path(__file__).parent / "results"),
                        help="Directory containing result JSON files")
    parser.add_argument("--output",
                        default=str(Path(__file__).parent / "results" / "analysis.json"),
                        help="Output path for analysis JSON")
    args = parser.parse_args()

    results = load_results(args.results_dir)
    if not results:
        print(f"No results found in {args.results_dir}")
        sys.exit(1)

    print(f"Loaded results for models: {list(results.keys())}")
    for model, conditions in results.items():
        for cond, runs in conditions.items():
            print(f"  {model}/{cond}: {len(runs)} runs, "
                  f"{sum(len(r) for r in runs)} total items")

    generate_report(results, args.output)


if __name__ == "__main__":
    main()
