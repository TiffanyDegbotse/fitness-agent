"""
FitAgent FastAPI Backend
Serves the agent API and Google OAuth endpoints.
"""

import json
import os
import urllib.parse
from typing import Any

import requests
from agent import run_agent
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="FitAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")


# ── Request / Response Models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    messages: list[dict] = []
    user_profile: dict | None = None
    step_data: list[dict] | None = None
    goal: dict | None = None


class ChatResponse(BaseModel):
    response: str
    messages: list[dict]


class GoalRequest(BaseModel):
    goal_type: str
    daily_target: float


# ── Chat Endpoint ─────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Main agent chat endpoint."""
    messages = req.messages + [{"role": "user", "content": req.message}]
    try:
        response_text, updated_messages = run_agent(
            messages=messages,
            user_profile=req.user_profile,
            step_data=req.step_data,
            goal=req.goal,
        )
        return ChatResponse(response=response_text, messages=updated_messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Apple Health Upload ───────────────────────────────────────────────────────

@app.post("/api/upload/apple-health")
async def upload_apple_health(file: UploadFile = File(...)):
    """Accept Apple Health export XML or CSV and return parsed step data."""
    from tools import parse_apple_health_csv

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    result = parse_apple_health_csv(text)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Google OAuth ──────────────────────────────────────────────────────────────

@app.get("/auth/google")
async def google_auth():
    """Redirect URL for Google OAuth."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/fitness.activity.read",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return {"auth_url": url}


@app.get("/auth/google/callback")
async def google_callback(code: str):
    """Exchange auth code for access token."""
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    tokens = resp.json()
    # In production, store refresh token securely. For now, return access token.
    return {"access_token": tokens.get("access_token"), "expires_in": tokens.get("expires_in")}


@app.post("/api/google-fit/steps")
async def get_google_fit_steps(body: dict):
    """Fetch steps from Google Fit using access token."""
    from tools import fetch_google_fit_steps

    access_token = body.get("access_token")
    days = body.get("days", 30)
    if not access_token:
        raise HTTPException(status_code=400, detail="access_token required")

    result = fetch_google_fit_steps(access_token, days)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}
