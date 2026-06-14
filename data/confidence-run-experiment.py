"""
Experiment: Self-Assessed Confidence vs Random (nogood-001 replication)

Tests whether LLM self-assessed confidence correlates with answer correctness,
or whether it's noise (or anti-correlated, as Kai Xu observed with Granite).

Three conditions:
  A: no-confidence  — answer directly, no self-assessment
  B: post-hoc       — answer, then rate confidence 1-10
  C: gated-revision — answer, rate confidence, revise if < 7

Usage:
  # Pilot run (8 questions, 1 model, 2 runs)
  python run_experiment.py --pilot

  # Full run (55 questions, 3 models, 5 runs)
  python run_experiment.py --full

  # Custom run
  python run_experiment.py --models claude-haiku-4-5-20250514 --conditions A B --runs 3

  # Single condition for debugging
  python run_experiment.py --models claude-sonnet-4-6-20250514 --conditions B --runs 1 --questions 3
"""

import argparse
import json
import os
import re
import signal
import sys
import time
from pathlib import Path


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("API call timed out")

# Add claude_code_langgraph to path so we can import its modules
LANGGRAPH_DIR = Path.home() / "git" / "claude_code_langgraph"
sys.path.insert(0, str(LANGGRAPH_DIR))

from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai.model_garden import ChatAnthropicVertex
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from main import get_langfuse_handler, invoke_agent, load_system_prompt
from tools import CORE_TOOLS

EVAL_DIR = Path.home() / "git" / "expert-service" / "eval"
RESULTS_DIR = Path(__file__).parent / "results"

# (provider, model_id, region)
MODELS = {
    "sonnet": ("anthropic", "claude-sonnet-4-6@default", "us-east5"),
    "opus": ("anthropic", "claude-opus-4-6@default", "us-east5"),
    "gemini-flash": ("gemini", "gemini-2.5-flash", "global"),
    "gemini-pro": ("gemini", "gemini-2.5-pro", "global"),
}

CONFIDENCE_PROMPT = (
    "\n\nNow rate your confidence in this answer on a scale of 1-10, "
    "where 1 means you are completely guessing and 10 means you are "
    "certain this is correct. Respond with just the number."
)

REVISION_PROMPT = (
    "Your confidence was {confidence}/10. Since your confidence is below 7, "
    "please reconsider your answer carefully. Look for errors or gaps in your "
    "reasoning, then provide your revised answer."
)

CONFIRM_PROMPT = (
    "Your confidence was {confidence}/10. Please confirm your original answer."
)


def build_model_graph(provider, model_id, region, tools=None):
    """Build a LangGraph agent for either Anthropic or Gemini models.

    If tools is an empty list, builds a simple graph with no tool access.
    If tools is None, defaults to CORE_TOOLS (for backward compatibility).
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("Error: set GOOGLE_CLOUD_PROJECT environment variable")
        sys.exit(1)

    if tools is None:
        tools = CORE_TOOLS

    if provider == "anthropic":
        model = ChatAnthropicVertex(
            model_name=model_id,
            project=project,
            location=region,
        )
    elif provider == "gemini":
        model = ChatVertexAI(
            model_name=model_id,
            project=project,
            location=region,
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

    if tools:
        model = model.bind_tools(tools)

    def agent(state: MessagesState):
        response = model.invoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent)
    graph.set_entry_point("agent")

    if tools:
        tool_node = ToolNode(tools)
        graph.add_node("tools", tool_node)

        def should_continue(state: MessagesState):
            last_message = state["messages"][-1]
            if last_message.tool_calls:
                return "tools"
            return END

        graph.add_conditional_edges("agent", should_continue)
        graph.add_edge("tools", "agent")
    else:
        graph.add_edge("agent", END)

    return graph.compile()


def normalize_response(response):
    """Normalize response to a string.

    Gemini returns a list of content blocks like [{"type": "text", "text": "..."}].
    Anthropic returns a plain string. Handle both.
    """
    if response is None:
        return None
    if isinstance(response, str):
        return response
    if isinstance(response, list):
        parts = []
        for block in response:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts) if parts else None
    return str(response)


def load_questions(n=None):
    """Load MC and OE questions from expert-service eval directory."""
    with open(EVAL_DIR / "questions.json") as f:
        mc_data = json.load(f)
    with open(EVAL_DIR / "open_ended.json") as f:
        oe_data = json.load(f)

    questions = []

    for q in mc_data["questions"]:
        choices_text = "\n".join(f"  {k}) {v}" for k, v in q["choices"].items())
        questions.append({
            "id": q["id"],
            "type": "mc",
            "text": f"{q['text']}\n{choices_text}",
            "correct": q["correct"],
            "objective": q.get("objective", ""),
        })

    for q in oe_data["questions"]:
        questions.append({
            "id": q["id"],
            "type": "oe",
            "text": q["text"],
            "rubric": q["rubric"],
            "category": q.get("category", ""),
        })

    if n:
        # Take first n MC and proportional OE
        mc = [q for q in questions if q["type"] == "mc"][:n]
        oe = [q for q in questions if q["type"] == "oe"][:max(1, n // 5)]
        questions = mc + oe

    return questions


def extract_confidence(text):
    """Extract a confidence rating (1-10) from model output."""
    if not text:
        return None
    # Look for a standalone number 1-10
    # Try "confidence: N" or "N/10" patterns first
    m = re.search(r"confidence[:\s]+(\d+)", text, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        if 1 <= val <= 10:
            return val
    m = re.search(r"(\d+)/10", text)
    if m:
        val = int(m.group(1))
        if 1 <= val <= 10:
            return val
    # Look for a standalone single digit or "10" on its own line
    for line in reversed(text.strip().split("\n")):
        line = line.strip().strip(".*")
        m = re.match(r"^(\d+)$", line)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 10:
                return val
    return None


def run_condition_a(app, system_prompt, question, langfuse_handler=None):
    """Condition A: No confidence — just answer the question."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question["text"]},
    ]
    start = time.time()
    result = invoke_agent(app, messages, langfuse_handler)
    duration = time.time() - start

    return {
        "condition": "A",
        "response": normalize_response(result["response"]),
        "confidence": None,
        "revised_response": None,
        "tool_calls": result["tool_calls"],
        "error": result["error"],
        "duration_s": round(duration, 2),
    }


def run_condition_b(app, system_prompt, question, langfuse_handler=None):
    """Condition B: Post-hoc confidence — answer, then rate confidence."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question["text"]},
    ]
    start = time.time()
    result = invoke_agent(app, messages, langfuse_handler)

    if result["error"]:
        duration = time.time() - start
        return {
            "condition": "B",
            "response": normalize_response(result["response"]),
            "confidence": None,
            "revised_response": None,
            "tool_calls": result["tool_calls"],
            "error": result["error"],
            "duration_s": round(duration, 2),
        }

    # Now ask for confidence
    messages = result["messages"]
    messages.append({"role": "user", "content": CONFIDENCE_PROMPT})
    conf_result = invoke_agent(app, messages, langfuse_handler)
    duration = time.time() - start

    confidence = extract_confidence(normalize_response(conf_result["response"]))

    return {
        "condition": "B",
        "response": normalize_response(result["response"]),
        "confidence": confidence,
        "confidence_raw": normalize_response(conf_result["response"]),
        "revised_response": None,
        "tool_calls": result["tool_calls"] + conf_result["tool_calls"],
        "error": conf_result["error"],
        "duration_s": round(duration, 2),
    }


def run_condition_c(app, system_prompt, question, langfuse_handler=None):
    """Condition C: Confidence-gated revision — answer, rate, revise if < 7."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question["text"]},
    ]
    start = time.time()
    result = invoke_agent(app, messages, langfuse_handler)

    if result["error"]:
        duration = time.time() - start
        return {
            "condition": "C",
            "response": normalize_response(result["response"]),
            "confidence": None,
            "revised_response": None,
            "tool_calls": result["tool_calls"],
            "error": result["error"],
            "duration_s": round(duration, 2),
        }

    original_response = normalize_response(result["response"])

    # Ask for confidence
    messages = result["messages"]
    messages.append({"role": "user", "content": CONFIDENCE_PROMPT})
    conf_result = invoke_agent(app, messages, langfuse_handler)

    confidence = extract_confidence(normalize_response(conf_result["response"]))

    if conf_result["error"] or confidence is None:
        duration = time.time() - start
        return {
            "condition": "C",
            "response": original_response,
            "confidence": confidence,
            "confidence_raw": normalize_response(conf_result["response"]),
            "revised_response": None,
            "tool_calls": result["tool_calls"] + conf_result["tool_calls"],
            "error": conf_result["error"] or "confidence_extraction_failed",
            "duration_s": round(duration, 2),
        }

    # Revise if low confidence, confirm if high
    messages = conf_result["messages"]
    if confidence < 7:
        revision_prompt = REVISION_PROMPT.format(confidence=confidence)
    else:
        revision_prompt = CONFIRM_PROMPT.format(confidence=confidence)
    messages.append({"role": "user", "content": revision_prompt})

    rev_result = invoke_agent(app, messages, langfuse_handler)
    duration = time.time() - start

    return {
        "condition": "C",
        "response": original_response,
        "confidence": confidence,
        "confidence_raw": conf_result["response"],
        "revised_response": normalize_response(rev_result["response"]),
        "revised": confidence < 7,
        "tool_calls": (result["tool_calls"] + conf_result["tool_calls"]
                       + rev_result["tool_calls"]),
        "error": rev_result["error"],
        "duration_s": round(duration, 2),
    }


CONDITION_RUNNERS = {
    "A": run_condition_a,
    "B": run_condition_b,
    "C": run_condition_c,
}


def run_experiment(models, conditions, questions, runs, output_dir,
                   start_run=1, tools=None):
    """Run the full experiment matrix."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = load_system_prompt()
    langfuse_handler = get_langfuse_handler()

    total_runs = len(models) * len(conditions) * len(questions) * runs
    completed = (start_run - 1) * len(models) * len(conditions) * len(questions)

    for model_name, model_spec in models.items():
        provider, model_id, region = model_spec
        print(f"\n{'='*60}")
        print(f"Model: {model_name} ({provider}/{model_id} @ {region})")
        print(f"{'='*60}")

        for condition in conditions:
            runner = CONDITION_RUNNERS[condition]
            print(f"\n  Condition {condition}:")

            for run_num in range(start_run, runs + 1):
                run_results = []
                # Build graph for this model
                app = build_model_graph(provider, model_id, region, tools=tools)

                for q in questions:
                    completed += 1
                    pct = completed / total_runs * 100
                    print(f"    [{completed}/{total_runs} {pct:.0f}%] "
                          f"Run {run_num} | {q['id']}: "
                          f"{q['text'][:50]}...")

                    # 5-minute timeout per question to prevent hangs
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(300)
                    try:
                        result = runner(app, system_prompt, q, langfuse_handler)
                    except TimeoutError:
                        print(f"    !! TIMEOUT on {q['id']}, skipping")
                        result = {
                            "condition": condition,
                            "response": None,
                            "confidence": None,
                            "revised_response": None,
                            "tool_calls": [],
                            "error": "timeout_300s",
                            "duration_s": 300.0,
                        }
                        app = build_model_graph(provider, model_id, region, tools=tools)
                    except Exception as e:
                        print(f"    !! ERROR on {q['id']}: {e!r}")
                        result = {
                            "condition": condition,
                            "response": None,
                            "confidence": None,
                            "revised_response": None,
                            "tool_calls": [],
                            "error": str(e)[:200],
                            "duration_s": 0.0,
                        }
                        app = build_model_graph(provider, model_id, region, tools=tools)
                    finally:
                        signal.alarm(0)

                    result["question_id"] = q["id"]
                    result["question_type"] = q["type"]
                    result["question_text"] = q["text"]
                    result["model"] = model_name
                    result["run"] = run_num

                    # Add ground truth for MC
                    if q["type"] == "mc":
                        result["correct_answer"] = q["correct"]

                    run_results.append(result)

                # Save results per model/condition/run
                out_file = output_dir / f"{model_name}_{condition}_run{run_num}.json"
                with open(out_file, "w") as f:
                    json.dump(run_results, f, indent=2)
                print(f"    -> Saved {out_file}")

    print(f"\n{'='*60}")
    print(f"Experiment complete: {completed} total runs")
    print(f"Results in {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Self-Assessed Confidence Experiment"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pilot", action="store_true",
                      help="Pilot run: 5 MC + 3 OE, 1 model (sonnet), 2 runs")
    mode.add_argument("--full", action="store_true",
                      help="Full run: all 55 questions, 3 models, 5 runs")

    parser.add_argument("--models", nargs="+",
                        choices=list(MODELS.keys()),
                        help="Which models to test")
    parser.add_argument("--conditions", nargs="+",
                        choices=["A", "B", "C"],
                        help="Which conditions to run")
    parser.add_argument("--runs", type=int, help="Number of runs per cell")
    parser.add_argument("--questions", type=int,
                        help="Limit number of MC questions (+ proportional OE)")
    parser.add_argument("--start-run", type=int, default=1,
                        help="Start from this run number (for resuming)")
    parser.add_argument("--with-tools", action="store_true",
                        help="Give models access to tools (default: no tools)")
    parser.add_argument("--output-dir", default=str(RESULTS_DIR),
                        help="Output directory for results")

    args = parser.parse_args()

    if args.pilot:
        models = {k: v for k, v in MODELS.items() if k == "sonnet"}
        conditions = ["A", "B", "C"]
        questions = load_questions(n=5)
        runs = 2
    elif args.full:
        models = {k: v for k, v in MODELS.items()
                  if k in ("sonnet", "opus")}
        conditions = ["A", "B", "C"]
        questions = load_questions()
        runs = 5
    else:
        model_keys = args.models or ["sonnet"]
        models = {k: MODELS[k] for k in model_keys}
        conditions = args.conditions or ["A", "B", "C"]
        questions = load_questions(n=args.questions)
        runs = args.runs or 1

    print(f"Experiment Configuration:")
    print(f"  Models:     {list(models.keys())}")
    print(f"  Conditions: {conditions}")
    print(f"  Questions:  {len(questions)} ({sum(1 for q in questions if q['type'] == 'mc')} MC, "
          f"{sum(1 for q in questions if q['type'] == 'oe')} OE)")
    print(f"  Runs:       {runs}")
    print(f"  Total:      {len(models) * len(conditions) * len(questions) * runs} invocations")
    print()

    tools = CORE_TOOLS if args.with_tools else []
    run_experiment(models, conditions, questions, runs, args.output_dir,
                   start_run=args.start_run, tools=tools)


if __name__ == "__main__":
    main()
