"""
FitAgent - LLM-powered fitness coaching agent.
Implements the agent loop (planning → tool selection → execution → response).
No frameworks used - pure Python agent loop.
"""
from dotenv import load_dotenv
load_dotenv()

import json
import os
from typing import Any
from anthropic import Anthropic
from tools import (
    calculate_calories,
    analyze_trends,
    get_fitness_advice,
    check_goal_progress,
    set_goal,
    parse_apple_health_csv,
    fetch_google_fit_steps,
)

client = Anthropic()

# Tool definitions passed to the LLM
TOOLS = [
    {
        "name": "calculate_calories",
        "description": (
            "Calculate calories burned from steps. Uses the user's weight, age, "
            "and step count to estimate calories burned using MET-based formula."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "steps": {"type": "number", "description": "Number of steps taken"},
                "weight_kg": {"type": "number", "description": "User weight in kilograms"},
                "age": {"type": "number", "description": "User age in years"},
                "height_cm": {"type": "number", "description": "User height in centimeters"},
            },
            "required": ["steps"],
        },
    },
    {
        "name": "analyze_trends",
        "description": (
            "Analyze step history to identify trends: weekly averages, best/worst days, "
            "streaks, and improvement or decline patterns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "step_data": {
                    "type": "array",
                    "description": "List of {date, steps} objects",
                    "items": {"type": "object"},
                }
            },
            "required": ["step_data"],
        },
    },
    {
        "name": "get_fitness_advice",
        "description": "Get personalized fitness advice based on performance and goals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "current_avg_steps": {"type": "number"},
                "goal_steps": {"type": "number"},
                "trend": {
                    "type": "string",
                    "enum": ["improving", "declining", "stable"],
                },
                "user_context": {"type": "string", "description": "Any extra context about the user"},
            },
            "required": ["current_avg_steps"],
        },
    },
    {
        "name": "set_goal",
        "description": "Set a weekly step or calorie goal for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal_type": {"type": "string", "enum": ["steps", "calories"]},
                "daily_target": {"type": "number", "description": "Daily target value"},
                "user_id": {"type": "string"},
            },
            "required": ["goal_type", "daily_target"],
        },
    },
    {
        "name": "check_goal_progress",
        "description": "Check how the user is progressing toward their current goal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "step_data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Recent step data",
                },
                "goal_steps": {"type": "number"},
                "goal_calories": {"type": "number"},
                "weight_kg": {"type": "number"},
                "age": {"type": "number"},
                "height_cm": {"type": "number"},
            },
            "required": ["step_data"],
        },
    },
    {
        "name": "parse_apple_health_csv",
        "description": "Parse an Apple Health export CSV/XML file and extract step data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_content": {
                    "type": "string",
                    "description": "Raw content of the Apple Health export file",
                }
            },
            "required": ["file_content"],
        },
    },
    {
        "name": "fetch_google_fit_steps",
        "description": "Fetch step count data from Google Fit for a given date range using an OAuth access token.",
        "input_schema": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string", "description": "Google OAuth access token"},
                "days": {"type": "number", "description": "Number of past days to fetch (default 30)"},
            },
            "required": ["access_token"],
        },
    },
]

TOOL_MAP = {
    "calculate_calories": calculate_calories,
    "analyze_trends": analyze_trends,
    "get_fitness_advice": get_fitness_advice,
    "set_goal": set_goal,
    "check_goal_progress": check_goal_progress,
    "parse_apple_health_csv": parse_apple_health_csv,
    "fetch_google_fit_steps": fetch_google_fit_steps,
}

SYSTEM_PROMPT = """You are FitAgent, a warm and motivating personal fitness coach powered by AI.

You help users understand their step counts, calories burned, activity trends, and fitness goals.
You have access to tools for calculating calories, analyzing trends, giving advice, and managing goals.

Guidelines:
- Be encouraging and positive, but honest about areas needing improvement
- Always use tools to back up your claims with data
- When a user shares health data, analyze it proactively
- If you need user stats (weight, age, height) for calorie calculations and don't have them, ask
- Keep responses concise but actionable
- Use emojis sparingly to keep things friendly without being over the top
"""


def run_agent(
    messages: list[dict],
    user_profile: dict | None = None,
    step_data: list[dict] | None = None,
    goal: dict | None = None,
) -> tuple[str, list[dict]]:
    """
    Core agent loop:
    1. Build context from user profile + data
    2. Send to LLM with tools
    3. If LLM calls a tool → execute it → feed result back → repeat
    4. Return final text response + updated messages
    """

    # Inject context into system prompt
    context_parts = [SYSTEM_PROMPT]
    if user_profile:
        context_parts.append(f"\nUser profile: {json.dumps(user_profile)}")
    if step_data:
        # Only send last 30 days to keep context manageable
        recent = step_data[-30:]
        context_parts.append(f"\nUser's recent step data (last {len(recent)} days): {json.dumps(recent)}")
    if goal:
        context_parts.append(f"\nUser's current goal: {json.dumps(goal)}")

    system = "\n".join(context_parts)

    # Agent loop
    loop_messages = list(messages)
    max_iterations = 10

    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=system,
            tools=TOOLS,
            messages=loop_messages,
        )

        # Collect assistant content blocks
        assistant_content = response.content
        loop_messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            # Extract final text
            final_text = " ".join(
                block.text for block in assistant_content if hasattr(block, "text")
            )
            return final_text, loop_messages

        if response.stop_reason == "tool_use":
            # Execute all tool calls
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    tool_fn = TOOL_MAP.get(block.name)
                    if tool_fn:
                        try:
                            result = tool_fn(**block.input)
                        except Exception as e:
                            result = {"error": str(e)}
                    else:
                        result = {"error": f"Unknown tool: {block.name}"}

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            loop_messages.append({"role": "user", "content": tool_results})
            continue

        break

    return "I'm sorry, I wasn't able to complete that request.", loop_messages
