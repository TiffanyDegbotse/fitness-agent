"""
FitAgent Evaluation Suite
Tests agent accuracy across tools and response quality.
Outputs quantitative scores to eval_results.json.
"""

import json
import math
import sys
import time
from typing import Any

# Add backend to path
sys.path.insert(0, "../backend")
from tools import (
    calculate_calories,
    analyze_trends,
    get_fitness_advice,
    set_goal,
    check_goal_progress,
    parse_apple_health_csv,
)

RESULTS = []


def score(name: str, passed: bool, expected: Any = None, actual: Any = None, note: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")
    if not passed and expected is not None:
        print(f"         expected={expected}, got={actual}")
    if note:
        print(f"         note: {note}")
    RESULTS.append({"test": name, "passed": passed, "expected": expected, "actual": actual, "note": note})


# ─────────────────────────────────────────────
# 1. Calorie Calculation Accuracy
# ─────────────────────────────────────────────
def eval_calories():
    print("\n── Tool 1: calculate_calories ──────────────────")
    # Known reference: 10,000 steps, 70kg, 30yo, 170cm → ~300-400 kcal typically
    result = calculate_calories(10000, 70.0, 30.0, 170.0)

    # Test: calories in plausible range
    cal = result["total_calories"]
    in_range = 250 <= cal <= 500
    score("10k steps calorie in range [250-500]", in_range, "250-500", cal)

    # Test: distance calculation
    dist = result["distance_km"]
    dist_ok = 6.0 <= dist <= 9.0
    score("10k steps distance in range [6-9 km]", dist_ok, "6-9", dist)

    # Test: zero steps returns zero calories
    r0 = calculate_calories(0, 70.0, 30.0, 170.0)
    score("0 steps → 0 calories", r0["total_calories"] == 0.0, 0.0, r0["total_calories"])

    # Test: heavier person burns more
    r_heavy = calculate_calories(10000, 100.0, 30.0, 170.0)
    r_light = calculate_calories(10000, 60.0, 30.0, 170.0)
    score("heavier person burns more calories", r_heavy["total_calories"] > r_light["total_calories"])

    # Test: more steps = more calories (monotonic)
    r5k = calculate_calories(5000)
    r10k = calculate_calories(10000)
    r15k = calculate_calories(15000)
    score("calorie monotonicity (5k < 10k < 15k)", r5k["total_calories"] < r10k["total_calories"] < r15k["total_calories"])

    # Accuracy test: compare to published estimate (Harvard: ~300 cal / 10k steps at 155lb)
    reference_cal = 300  # conservative reference
    error_pct = abs(cal - reference_cal) / reference_cal * 100
    score("calorie estimate within 40% of Harvard reference", error_pct < 40, f"±40% of {reference_cal}", round(cal, 1), f"error={round(error_pct,1)}%")


# ─────────────────────────────────────────────
# 2. Trend Analysis Accuracy
# ─────────────────────────────────────────────
def eval_trends():
    print("\n── Tool 2: analyze_trends ──────────────────────")

    improving_data = [
        {"date": f"2024-01-{i+1:02d}", "steps": 5000 + i * 200} for i in range(20)
    ]
    result = analyze_trends(improving_data)
    score("improving trend detected", result["trend"] == "improving", "improving", result["trend"])

    declining_data = [
        {"date": f"2024-02-{i+1:02d}", "steps": 9000 - i * 200} for i in range(20)
    ]
    result2 = analyze_trends(declining_data)
    score("declining trend detected", result2["trend"] == "declining", "declining", result2["trend"])

    stable_data = [
        {"date": f"2024-03-{i+1:02d}", "steps": 8000 + ((-1) ** i * 100)} for i in range(20)
    ]
    result3 = analyze_trends(stable_data)
    score("stable trend detected", result3["trend"] == "stable", "stable", result3["trend"])

    # Streak test: 5 consecutive days above 8000
    streak_data = [
        {"date": "2024-04-01", "steps": 3000},
        {"date": "2024-04-02", "steps": 8500},
        {"date": "2024-04-03", "steps": 9000},
        {"date": "2024-04-04", "steps": 8200},
        {"date": "2024-04-05", "steps": 8800},
        {"date": "2024-04-06", "steps": 9100},
    ]
    result4 = analyze_trends(streak_data)
    score("current streak = 5", result4["current_streak_days"] == 5, 5, result4["current_streak_days"])

    # Average accuracy
    avg_data = [{"date": f"2024-05-{i+1:02d}", "steps": 7000} for i in range(10)]
    result5 = analyze_trends(avg_data)
    score("average_daily_steps correct (all 7000)", result5["average_daily_steps"] == 7000, 7000, result5["average_daily_steps"])

    # Empty data
    result6 = analyze_trends([])
    score("empty data returns error", "error" in result6)


# ─────────────────────────────────────────────
# 3. Fitness Advice Quality
# ─────────────────────────────────────────────
def eval_advice():
    print("\n── Tool 3: get_fitness_advice ──────────────────")

    # Exceeding goal
    r = get_fitness_advice(12000, 10000, "improving")
    score("exceeding goal → correct tier", r["tier"] == "exceeding_goal", "exceeding_goal", r["tier"])
    score("exceeding goal → 0 steps to goal", r["steps_to_goal"] == 0, 0, r["steps_to_goal"])

    # Close to goal
    r2 = get_fitness_advice(8500, 10000, "stable")
    score("close to goal tier (85%)", r2["tier"] == "close_to_goal", "close_to_goal", r2["tier"])

    # Halfway
    r3 = get_fitness_advice(5000, 10000, "declining")
    score("halfway tier (50%)", r3["tier"] == "halfway", "halfway", r3["tier"])

    # Getting started
    r4 = get_fitness_advice(2000, 10000)
    score("getting started tier (20%)", r4["tier"] == "getting_started", "getting_started", r4["tier"])

    # Tips non-empty
    score("advice includes actionable tips", len(r4["actionable_tips"]) >= 2)

    # Improving trend message
    r5 = get_fitness_advice(9000, 10000, "improving")
    score("improving trend message present", "improving" in r5["trend_message"].lower() or "momentum" in r5["trend_message"].lower())


# ─────────────────────────────────────────────
# 4. Goal Setting & Progress
# ─────────────────────────────────────────────
def eval_goals():
    print("\n── Tools 4 & 5: set_goal / check_goal_progress ─")

    r = set_goal("steps", 10000, "test_user")
    score("set_goal success", r["success"] is True)
    score("set_goal type correct", r["goal"]["type"] == "steps", "steps", r["goal"]["type"])

    # Invalid
    r2 = set_goal("miles", 5, "test_user")
    score("invalid goal_type returns error", "error" in r2)

    # Check progress
    from datetime import datetime, timedelta
    today = datetime.now()
    step_data = [
        {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "steps": 10500 if i % 2 == 0 else 7000}
        for i in range(7)
    ]
    r3 = check_goal_progress(step_data, goal_steps=10000, user_id="test_user")
    score("check_goal_progress returns days_met", "days_met_step_goal" in r3)
    met = r3["days_met_step_goal"]
    score("days met step goal is 0-7", 0 <= met <= 7, "0-7", met)


# ─────────────────────────────────────────────
# 5. Apple Health Parser
# ─────────────────────────────────────────────
def eval_parser():
    print("\n── Tool 6: parse_apple_health_csv ──────────────")

    # CSV
    csv_content = "date,steps\n2024-01-01,8500\n2024-01-02,10200\n2024-01-03,6000\n"
    r = parse_apple_health_csv(csv_content)
    score("CSV parse: days_found = 3", r["days_found"] == 3, 3, r["days_found"])
    score("CSV parse: first steps = 8500", r["step_data"][0]["steps"] == 8500, 8500, r["step_data"][0]["steps"])

    # Case-insensitive columns
    csv2 = "Date,Steps\n2024-02-01,9999\n"
    r2 = parse_apple_health_csv(csv2)
    score("CSV parse: capital columns work", r2["days_found"] == 1, 1, r2.get("days_found"))

    # Minimal XML
    xml_content = """<?xml version="1.0"?>
<HealthData>
  <Record type="HKQuantityTypeIdentifierStepCount" startDate="2024-01-01 00:00:00" value="4000"/>
  <Record type="HKQuantityTypeIdentifierStepCount" startDate="2024-01-01 12:00:00" value="3000"/>
  <Record type="HKQuantityTypeIdentifierStepCount" startDate="2024-01-02 00:00:00" value="9500"/>
</HealthData>"""
    r3 = parse_apple_health_csv(xml_content)
    score("XML parse: 2 unique days", r3.get("days_found") == 2, 2, r3.get("days_found"))
    # 4000+3000 should be aggregated to 7000 on day 1
    day1 = next((d for d in r3.get("step_data", []) if d["date"] == "2024-01-01"), None)
    score("XML parse: day 1 steps aggregated = 7000", day1 and day1["steps"] == 7000, 7000, day1)

    # Bad input
    r4 = parse_apple_health_csv("garbage data no columns")
    score("bad CSV returns error", "error" in r4)


# ─────────────────────────────────────────────
# Run all evals
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  FitAgent Evaluation Suite")
    print("=" * 55)

    eval_calories()
    eval_trends()
    eval_advice()
    eval_goals()
    eval_parser()

    # Summary
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = total - passed
    pct = round(passed / total * 100, 1) if total else 0

    print("\n" + "=" * 55)
    print(f"  RESULTS: {passed}/{total} passed ({pct}%)")
    print(f"  Failed:  {failed}")
    print("=" * 55)

    # Save JSON results
    summary = {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate_pct": pct,
        "tests": RESULTS,
    }
    with open("eval_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\n  Results saved to eval/eval_results.json")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
