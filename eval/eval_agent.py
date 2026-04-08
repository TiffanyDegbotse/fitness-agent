"""
FitAgent — Full Agent Evaluation
Tests the complete agent loop end-to-end by sending real messages
and scoring the quality of responses quantitatively.

"""

import json
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, "../backend")
from dotenv import load_dotenv
load_dotenv("../backend/.env")
from agent import run_agent

RESULTS = []

# ── Sample data used across all tests ─────────────────────────────────────────
SAMPLE_STEP_DATA = [
    {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
     "steps": [9200, 7800, 11000, 8500, 10200, 6500, 9800, 10500, 7200, 8900,
               11200, 9400, 8100, 10800, 7600, 9300, 11500, 8700, 9100, 10300,
               7400, 8800, 10600, 9500, 8200, 11100, 7900, 9700, 10100, 8400][i]}
    for i in range(30)
]

USER_PROFILE = {
    "name": "TestUser",
    "age": 28,
    "weight_kg": 70,
    "height_cm": 170,
}

GOAL = {"type": "steps", "daily_target": 10000}


def score_response(test_name, response, criteria, elapsed):
    """Score a response against a list of criteria functions."""
    passed = sum(1 for _, fn in criteria if fn(response))
    total = len(criteria)
    pct = round(passed / total * 100)

    print(f"\n  [{test_name}]")
    print(f"  Response preview: {response[:120]}...")
    for label, fn in criteria:
        status = "✓" if fn(response) else "✗"
        print(f"    {status} {label}")
    print(f"  Score: {passed}/{total} ({pct}%) — {round(elapsed, 2)}s")

    RESULTS.append({
        "test": test_name,
        "score": pct,
        "passed_criteria": passed,
        "total_criteria": total,
        "response_time_s": round(elapsed, 2),
        "response_preview": response[:200],
    })
    return pct


def run(message, context=True):
    """Run the agent with a message and return (response, elapsed_seconds)."""
    messages = [{"role": "user", "content": message}]
    start = time.time()
    response, _ = run_agent(
        messages=messages,
        user_profile=USER_PROFILE if context else None,
        step_data=SAMPLE_STEP_DATA if context else None,
        goal=GOAL if context else None,
    )
    elapsed = time.time() - start
    return response, elapsed


# ── Test 1: Weekly Summary ─────────────────────────────────────────────────────
def test_weekly_summary():
    response, elapsed = run("How am I doing this week?")
    criteria = [
        ("mentions steps or step count",
            lambda r: "step" in r.lower()),
        ("includes a number (actual data used)",
            lambda r: any(c.isdigit() for c in r)),
        ("gives an assessment (good/great/well/behind/below/above)",
            lambda r: any(w in r.lower() for w in ["good", "great", "well", "behind", "below", "above", "excellent", "nice", "strong"])),
        ("mentions the goal",
            lambda r: "goal" in r.lower() or "10,000" in r or "10000" in r),
        ("response is substantial (>50 chars)",
            lambda r: len(r) > 50),
    ]
    return score_response("Weekly Summary", response, criteria, elapsed)


# ── Test 2: Calorie Query ──────────────────────────────────────────────────────
def test_calorie_query():
    response, elapsed = run("How many calories did I burn yesterday?")
    criteria = [
        ("mentions calories",
            lambda r: "calor" in r.lower()),
        ("includes a number",
            lambda r: any(c.isdigit() for c in r)),
        ("response is substantial (>50 chars)",
            lambda r: len(r) > 50),
        ("mentions steps or walking",
            lambda r: "step" in r.lower() or "walk" in r.lower()),
        ("gives a specific calorie estimate (3 digits)",
            lambda r: any(r[i:i+3].isdigit() for i in range(len(r)-2))),
    ]
    return score_response("Calorie Query", response, criteria, elapsed)


# ── Test 3: Trend Analysis ─────────────────────────────────────────────────────
def test_trend_analysis():
    response, elapsed = run("Analyze my step trends over the past month")
    criteria = [
        ("mentions trend direction (improving/declining/stable)",
            lambda r: any(w in r.lower() for w in ["improving", "declining", "stable", "consistent", "increase", "decrease"])),
        ("mentions average steps",
            lambda r: "average" in r.lower() or "avg" in r.lower()),
        ("includes numbers",
            lambda r: any(c.isdigit() for c in r)),
        ("mentions streak or consecutive days",
            lambda r: any(w in r.lower() for w in ["streak", "consecutive", "row", "days in"])),
        ("response is detailed (>100 chars)",
            lambda r: len(r) > 100),
    ]
    return score_response("Trend Analysis", response, criteria, elapsed)


# ── Test 4: Goal Setting ───────────────────────────────────────────────────────
def test_goal_setting():
    response, elapsed = run("Set my daily step goal to 8,000 steps")
    criteria = [
        ("acknowledges the goal was set",
            lambda r: any(w in r.lower() for w in ["set", "updated", "saved", "goal", "done", "great"])),
        ("mentions 8000 or 8,000",
            lambda r: "8000" in r or "8,000" in r),
        ("positive/confirmatory tone",
            lambda r: any(w in r.lower() for w in ["great", "done", "set", "perfect", "good", "success", "!"])),
        ("response is not empty",
            lambda r: len(r) > 10),
        ("does not return an error",
            lambda r: "error" not in r.lower() and "❌" not in r),
    ]
    return score_response("Goal Setting", response, criteria, elapsed)


# ── Test 5: Personalized Advice ────────────────────────────────────────────────
def test_personalized_advice():
    response, elapsed = run("Give me tips to increase my step count")
    criteria = [
        ("gives actionable tips",
            lambda r: any(w in r.lower() for w in ["try", "walk", "take", "use", "park", "stairs", "remind", "tip"])),
        ("response is detailed (>100 chars)",
            lambda r: len(r) > 100),
        ("multiple suggestions (contains list indicators)",
            lambda r: r.count("\n") >= 2 or any(w in r for w in ["1.", "2.", "-", "•", "*"])),
        ("personalized to user data",
            lambda r: any(w in r.lower() for w in ["step", "goal", "average", "week", "daily"])),
        ("encouraging tone",
            lambda r: any(w in r.lower() for w in ["great", "good", "can", "will", "keep", "!", "you're", "you are"])),
    ]
    return score_response("Personalized Advice", response, criteria, elapsed)


# ── Test 6: Goal Progress Check ────────────────────────────────────────────────
def test_goal_progress():
    response, elapsed = run("How many days did I hit my step goal this week?")
    criteria = [
        ("mentions number of days",
            lambda r: any(c.isdigit() for c in r)),
        ("mentions the goal",
            lambda r: "goal" in r.lower()),
        ("mentions days or week",
            lambda r: "day" in r.lower() or "week" in r.lower()),
        ("response is substantial (>50 chars)",
            lambda r: len(r) > 50),
        ("does not return an error",
            lambda r: "error" not in r.lower() and "❌" not in r),
    ]
    return score_response("Goal Progress Check", response, criteria, elapsed)


# ── Test 7: No Data Context ────────────────────────────────────────────────────
def test_no_data_graceful():
    """Agent should handle missing data gracefully."""
    response, elapsed = run("How am I doing?", context=False)
    criteria = [
        ("does not crash",
            lambda r: len(r) > 0),
        ("asks for data or explains limitation",
            lambda r: any(w in r.lower() for w in ["upload", "data", "don't have", "no data", "provide", "share", "import"])),
        ("still helpful (gives guidance)",
            lambda r: len(r) > 40),
        ("polite and friendly tone",
            lambda r: any(w in r.lower() for w in ["happy", "help", "please", "sure", "can", "would", "!"])),
        ("does not return a raw error",
            lambda r: "traceback" not in r.lower() and "exception" not in r.lower()),
    ]
    return score_response("No Data — Graceful Handling", response, criteria, elapsed)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  FitAgent — Full Agent Evaluation")
    print("  Tests the complete agent loop end-to-end")
    print("=" * 60)
    print(f"\n  User profile: {USER_PROFILE['name']}, {USER_PROFILE['age']}yo")
    print(f"  Step data: {len(SAMPLE_STEP_DATA)} days")
    print(f"  Goal: {GOAL['daily_target']:,} steps/day")
    print("\n  Running tests (each makes a live API call)...\n")

    scores = []
    scores.append(test_weekly_summary())
    scores.append(test_calorie_query())
    scores.append(test_trend_analysis())
    scores.append(test_goal_setting())
    scores.append(test_personalized_advice())
    scores.append(test_goal_progress())
    scores.append(test_no_data_graceful())

    # Summary
    avg_score = round(sum(scores) / len(scores), 1)
    avg_time = round(sum(r["response_time_s"] for r in RESULTS) / len(RESULTS), 2)
    perfect = sum(1 for s in scores if s == 100)

    print("\n" + "=" * 60)
    print(f"  AGENT EVALUATION RESULTS")
    print(f"  Tests run:          {len(scores)}")
    print(f"  Average quality:    {avg_score}%")
    print(f"  Perfect scores:     {perfect}/{len(scores)}")
    print(f"  Avg response time:  {avg_time}s")
    print("=" * 60)

    # Per-test summary
    print("\n  Per-test breakdown:")
    for r in RESULTS:
        bar = "█" * (r["score"] // 10) + "░" * (10 - r["score"] // 10)
        print(f"  {r['test']:<30} {bar} {r['score']}%  ({r['response_time_s']}s)")

    # Save results
    summary = {
        "agent_quality_score_pct": avg_score,
        "tests_run": len(scores),
        "perfect_scores": perfect,
        "avg_response_time_s": avg_time,
        "individual_scores": RESULTS,
    }
    with open("eval_agent_results.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Results saved to eval/eval_agent_results.json")
    print(f"\n  ✅ Overall agent quality score: {avg_score}%")

    return 0 if avg_score >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())
