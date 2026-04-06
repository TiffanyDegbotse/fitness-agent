"""
FitAgent Tools
All tool functions used by the agent loop.
"""

import csv
import io
import json
import math
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

import requests


# ─────────────────────────────────────────────
# Tool 1: Calculate Calories
# ─────────────────────────────────────────────
def calculate_calories(
    steps: float,
    weight_kg: float = 70.0,
    age: float = 30.0,
    height_cm: float = 170.0,
) -> dict:
    """
    Estimate calories burned from steps using a MET-based formula.
    MET for walking ≈ 3.5. Adjusted by stride length and pace.
    """
    # Estimate distance in km from steps (avg stride ~0.762m)
    stride_m = 0.413 * (height_cm / 100)  # height-adjusted stride
    distance_km = (steps * stride_m) / 1000

    # Estimate duration: avg walking pace ~5 km/h
    pace_kmh = 5.0
    duration_hours = distance_km / pace_kmh

    # MET-based calorie formula: calories = MET * weight_kg * duration_hours
    MET = 3.5
    calories = MET * weight_kg * duration_hours

    # Active calories (subtract BMR contribution)
    bmr_per_hour = (10 * weight_kg + 6.25 * height_cm - 5 * age) / 24
    active_calories = max(calories - bmr_per_hour * duration_hours, calories * 0.7)

    return {
        "steps": int(steps),
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_hours * 60, 1),
        "total_calories": round(calories, 1),
        "active_calories": round(active_calories, 1),
        "formula": "MET-based (MET=3.5, height-adjusted stride)",
    }


# ─────────────────────────────────────────────
# Tool 2: Analyze Trends
# ─────────────────────────────────────────────
def analyze_trends(step_data: list[dict]) -> dict:
    """
    Analyze step history. Expects list of {date: str, steps: int}.
    Returns weekly averages, best/worst days, streaks, trend direction.
    """
    if not step_data:
        return {"error": "No step data provided"}

    # Sort by date
    try:
        sorted_data = sorted(step_data, key=lambda x: x["date"])
    except KeyError:
        return {"error": "Each entry must have 'date' and 'steps' fields"}

    steps_list = [int(d["steps"]) for d in sorted_data]
    dates_list = [d["date"] for d in sorted_data]

    avg_steps = sum(steps_list) / len(steps_list)
    max_steps = max(steps_list)
    min_steps = min(steps_list)
    best_day = dates_list[steps_list.index(max_steps)]
    worst_day = dates_list[steps_list.index(min_steps)]

    # Weekly averages
    weekly: dict[str, list] = {}
    for d in sorted_data:
        try:
            dt = datetime.strptime(d["date"][:10], "%Y-%m-%d")
            week_key = dt.strftime("%Y-W%W")
            weekly.setdefault(week_key, []).append(int(d["steps"]))
        except ValueError:
            continue

    weekly_avgs = {w: round(sum(v) / len(v)) for w, v in weekly.items()}

    # Trend: compare first half vs second half
    mid = len(steps_list) // 2
    first_half_avg = sum(steps_list[:mid]) / max(mid, 1)
    second_half_avg = sum(steps_list[mid:]) / max(len(steps_list) - mid, 1)
    if second_half_avg > first_half_avg * 1.05:
        trend = "improving"
    elif second_half_avg < first_half_avg * 0.95:
        trend = "declining"
    else:
        trend = "stable"

    # Streak: consecutive days hitting 8000+ steps
    goal_threshold = 8000
    current_streak = 0
    max_streak = 0
    temp_streak = 0
    for s in steps_list:
        if s >= goal_threshold:
            temp_streak += 1
            max_streak = max(max_streak, temp_streak)
        else:
            temp_streak = 0
    # Current streak (from end)
    for s in reversed(steps_list):
        if s >= goal_threshold:
            current_streak += 1
        else:
            break

    # Days above 10k
    days_above_10k = sum(1 for s in steps_list if s >= 10000)

    return {
        "total_days": len(steps_list),
        "average_daily_steps": round(avg_steps),
        "max_steps": max_steps,
        "min_steps": min_steps,
        "best_day": best_day,
        "worst_day": worst_day,
        "trend": trend,
        "first_half_avg": round(first_half_avg),
        "second_half_avg": round(second_half_avg),
        "weekly_averages": weekly_avgs,
        "current_streak_days": current_streak,
        "longest_streak_days": max_streak,
        "days_above_10k": days_above_10k,
        "pct_days_above_10k": round(days_above_10k / len(steps_list) * 100, 1),
    }


# ─────────────────────────────────────────────
# Tool 3: Get Fitness Advice
# ─────────────────────────────────────────────
def get_fitness_advice(
    current_avg_steps: float,
    goal_steps: float = 10000,
    trend: str = "stable",
    user_context: str = "",
) -> dict:
    """
    Return structured, evidence-based fitness advice based on performance.
    """
    gap = goal_steps - current_avg_steps
    pct_of_goal = (current_avg_steps / goal_steps) * 100 if goal_steps else 0

    # Tier-based advice
    if pct_of_goal >= 100:
        tier = "exceeding_goal"
        primary_advice = "You're crushing your goal! Consider increasing your target or adding intensity with incline walks."
        tips = [
            "Try interval walking: alternate 2 min fast, 1 min slow",
            "Add a weekend hike to boost weekly totals",
            "Consider a 12,000 step stretch goal",
        ]
    elif pct_of_goal >= 80:
        tier = "close_to_goal"
        primary_advice = f"You're {round(gap)} steps away from your daily goal — just a 15-20 min walk!"
        tips = [
            "Take a short walk after dinner (20 min ≈ 2,000 steps)",
            "Park further away or get off transit one stop early",
            "Use a standing desk or take walking meetings",
        ]
    elif pct_of_goal >= 50:
        tier = "halfway"
        primary_advice = "You're halfway there. Small habit changes can close the gap quickly."
        tips = [
            "Set hourly reminders to take a 5-min walk",
            "Walk during phone calls",
            "Morning 10-min walk before work adds ~1,000 steps",
            "Take stairs instead of elevators",
        ]
    else:
        tier = "getting_started"
        primary_advice = "Let's build your step habit gradually. Increase by 500 steps per week."
        tips = [
            "Start with a 10-minute walk once a day",
            "Walk to the nearest coffee shop instead of driving",
            "Short walks after each meal add up fast",
            "Track your steps to stay aware and motivated",
        ]

    trend_message = {
        "improving": "Your trend is going up — great momentum, keep it going!",
        "declining": "Your steps have dipped recently. Life gets busy, but even small walks help.",
        "stable": "Your activity is consistent. Ready to push to the next level?",
    }.get(trend, "")

    return {
        "tier": tier,
        "percent_of_goal": round(pct_of_goal, 1),
        "steps_to_goal": round(gap) if gap > 0 else 0,
        "primary_advice": primary_advice,
        "trend_message": trend_message,
        "actionable_tips": tips,
        "estimated_minutes_to_close_gap": round(gap / 100) if gap > 0 else 0,
    }


# ─────────────────────────────────────────────
# Tool 4: Set Goal
# ─────────────────────────────────────────────

# In-memory goal store (in production, use a DB)
_goals: dict[str, dict] = {}


def set_goal(
    goal_type: str,
    daily_target: float,
    user_id: str = "default",
) -> dict:
    """Set a daily step or calorie goal for the user."""
    if goal_type not in ("steps", "calories"):
        return {"error": "goal_type must be 'steps' or 'calories'"}
    if daily_target <= 0:
        return {"error": "daily_target must be positive"}

    goal = {
        "type": goal_type,
        "daily_target": daily_target,
        "set_at": datetime.now().isoformat(),
    }
    _goals[user_id] = goal

    return {
        "success": True,
        "goal": goal,
        "message": f"Goal set: {int(daily_target):,} {goal_type} per day",
    }


# ─────────────────────────────────────────────
# Tool 5: Check Goal Progress
# ─────────────────────────────────────────────
def check_goal_progress(
    step_data: list[dict],
    goal_steps: float | None = None,
    goal_calories: float | None = None,
    weight_kg: float = 70.0,
    age: float = 30.0,
    height_cm: float = 170.0,
    user_id: str = "default",
) -> dict:
    """Check how the user is progressing against their goal this week."""
    # Use stored goal if not provided
    stored = _goals.get(user_id, {})
    if goal_steps is None and stored.get("type") == "steps":
        goal_steps = stored["daily_target"]
    if goal_calories is None and stored.get("type") == "calories":
        goal_calories = stored["daily_target"]

    # Last 7 days
    today = datetime.now().date()
    week_data = []
    for d in step_data:
        try:
            dt = datetime.strptime(d["date"][:10], "%Y-%m-%d").date()
            if (today - dt).days < 7:
                week_data.append(d)
        except ValueError:
            continue

    if not week_data:
        return {"error": "No data for the past 7 days"}

    steps_this_week = [int(d["steps"]) for d in week_data]
    avg = sum(steps_this_week) / len(steps_this_week)

    results: dict[str, Any] = {
        "days_tracked_this_week": len(week_data),
        "average_daily_steps": round(avg),
    }

    if goal_steps:
        days_met = sum(1 for s in steps_this_week if s >= goal_steps)
        results["goal_steps"] = goal_steps
        results["days_met_step_goal"] = days_met
        results["step_goal_completion_pct"] = round(days_met / len(steps_this_week) * 100, 1)
        results["avg_vs_goal"] = round(avg - goal_steps)

    if goal_calories:
        cal_days = [
            calculate_calories(s, weight_kg, age, height_cm)["active_calories"]
            for s in steps_this_week
        ]
        avg_cal = sum(cal_days) / len(cal_days)
        days_met_cal = sum(1 for c in cal_days if c >= goal_calories)
        results["goal_calories"] = goal_calories
        results["average_daily_active_calories"] = round(avg_cal, 1)
        results["days_met_calorie_goal"] = days_met_cal

    return results


# ─────────────────────────────────────────────
# Tool 6: Parse Apple Health CSV/XML Export
# ─────────────────────────────────────────────
def parse_apple_health_csv(file_content: str) -> dict:
    """
    Parse Apple Health export. Supports:
    - export.xml (full Apple Health export)
    - Simple CSV with date,steps columns
    """
    file_content = file_content.strip()

    # Try XML first
    if file_content.startswith("<?xml") or "<HealthData" in file_content:
        return _parse_apple_health_xml(file_content)

    # Try CSV
    return _parse_steps_csv(file_content)


def _parse_apple_health_xml(xml_content: str) -> dict:
    """Parse Apple Health export.xml for step counts."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return {"error": f"Invalid XML: {e}"}

    daily_steps: dict[str, int] = {}
    for record in root.findall(".//Record"):
        if record.get("type") == "HKQuantityTypeIdentifierStepCount":
            try:
                start = record.get("startDate", "")[:10]
                value = int(float(record.get("value", 0)))
                daily_steps[start] = daily_steps.get(start, 0) + value
            except (ValueError, TypeError):
                continue

    step_data = [{"date": d, "steps": s} for d, s in sorted(daily_steps.items())]
    return {
        "source": "Apple Health XML",
        "days_found": len(step_data),
        "step_data": step_data,
    }


def _parse_steps_csv(csv_content: str) -> dict:
    """Parse a simple CSV with date and steps columns."""
    reader = csv.DictReader(io.StringIO(csv_content))
    step_data = []
    for row in reader:
        # Try common column name variations
        date_val = row.get("date") or row.get("Date") or row.get("startDate")
        steps_val = row.get("steps") or row.get("Steps") or row.get("value") or row.get("step_count")
        if date_val and steps_val:
            try:
                step_data.append({"date": date_val[:10], "steps": int(float(steps_val))})
            except (ValueError, TypeError):
                continue

    if not step_data:
        return {"error": "Could not find date/steps columns in CSV"}

    return {
        "source": "CSV upload",
        "days_found": len(step_data),
        "step_data": sorted(step_data, key=lambda x: x["date"]),
    }


# ─────────────────────────────────────────────
# Tool 7: Fetch Google Fit Steps
# ─────────────────────────────────────────────
def fetch_google_fit_steps(access_token: str, days: int = 30) -> dict:
    """
    Fetch daily step counts from Google Fit REST API.
    Requires a valid OAuth2 access token with fitness.activity.read scope.
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)

    # Google Fit aggregation request
    url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {
        "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
        "bucketByTime": {"durationMillis": 86400000},  # 1 day buckets
        "startTimeMillis": int(start_time.timestamp() * 1000),
        "endTimeMillis": int(end_time.timestamp() * 1000),
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Google Fit API error: {str(e)}"}

    data = resp.json()
    step_data = []
    for bucket in data.get("bucket", []):
        start_ms = int(bucket["startTimeMillis"])
        date_str = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        steps = 0
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                for val in point.get("value", []):
                    steps += val.get("intVal", 0)
        step_data.append({"date": date_str, "steps": steps})

    return {
        "source": "Google Fit",
        "days_fetched": len(step_data),
        "step_data": step_data,
    }
