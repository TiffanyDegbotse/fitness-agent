# FitAgent 🏃 AI-Powered Fitness Coach

FitAgent is an LLM-based agent that acts as your personal fitness coach. It analyzes your step data, calculates calories burned, identifies trends, and gives personalized advice, all through a conversational chat interface.

## Features

- **Agent loop**
- **6 tools** the agent can call: calorie calculator, trend analyzer, fitness advice engine, goal setter, goal progress tracker, CSV parser
- **React dashboard** with interactive charts 
- **Chat interface** to talk to the agent naturally
- **Two evaluation suites** — tool accuracy tests (30 tests, 100%) and full agent quality tests (7 scenarios, 97.1%)

---

## Project Structure

```
fitness-agent/
├── backend/
│   ├── agent.py          # Agent loop (planning + tool-calling)
│   ├── tools.py          # All 6 tool implementations
│   ├── main.py           # FastAPI server + endpoints
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Setup.jsx      # Profile + data import
│   │   │   ├── Dashboard.jsx  # Charts + stats
│   │   │   └── Chat.jsx       # Agent chat UI
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── eval/
│   ├── eval.py                # Tool accuracy test suite (30 tests)
│   ├── eval_agent.py          # Full agent loop evaluation (7 scenarios)
│   ├── eval_results.json      # Generated after running eval.py
│   └── eval_agent_results.json # Generated after running eval_agent.py
├── data/
│   └── samples/
│       └── sample_steps.csv   # Demo data for testing
└── README.md
```

---

## How to Run Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- An Anthropic API key (https://console.anthropic.com)

---

### Step 1 — Backend Setup

```bash
cd fitness-agent/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables — add your ANTHROPIC_API_KEY
cp .env.example .env
```

Start the backend:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000

---

### Step 2 — Frontend Setup

Open a new terminal:

```bash
cd fitness-agent/frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

---

### Step 3 — Use the App

1. **Setup page**: Enter your profile (name, age, weight, height) and set a daily goal
2. **Import data**: Upload a CSV file with `date` and `steps` columns
3. **Dashboard**: View your step charts and stats
4. **Chat**: Ask FitAgent anything, it uses tools automatically

**Quick test with sample data**: Upload `data/samples/sample_steps.csv` on the Setup page.

---

## Running the Evaluation Suites

### Suite 1 — Tool Accuracy (30 tests, deterministic)
Tests each tool directly with known inputs and expected outputs. No API calls needed.

```bash
cd fitness-agent/eval
python eval.py
```

Results saved to `eval/eval_results.json`

What it tests:
- **Calorie accuracy**: Validates against MET formula and Harvard reference values (14.7% error)
- **Trend detection**: Tests improving/declining/stable classification
- **Advice quality**: Checks tier assignments and tip generation
- **Goal tracking**: Tests set/check goal flows
- **Parser robustness**: Tests CSV parsing including edge cases and bad input

**Result: 30/30 passed (100%)**

---

### Suite 2 — Full Agent Evaluation (7 scenarios, live API calls)
Tests the complete agent loop end-to-end. Sends real messages to Claude, scores response quality against criteria.

```bash
cd fitness-agent/eval
python eval_agent.py
```

Results saved to `eval/eval_agent_results.json`

What it tests:
- **Weekly summary**: Does the agent use real data and give an assessment?
- **Calorie query**: Does it return a specific, accurate calorie estimate?
- **Trend analysis**: Does it identify trends and mention streaks?
- **Goal setting**: Does it confirm the goal and mention the correct number?
- **Personalized advice**: Does it give multiple actionable, personalized tips?
- **Goal progress**: Does it report how many days the goal was hit?
- **No data handling**: Does it handle missing data gracefully without crashing?

**Result: 97.1% average quality score (6/7 perfect)**

Note: The one 80% score (Goal Progress Check) is a false negative — the agent answered correctly but the evaluation criterion matched the word "error" appearing naturally in Claude's response rather than an actual system error. This highlights the challenge of evaluating natural language outputs with exact string matching.

---

## Agent Design

The agent loop is in `backend/agent.py`:

1. **Context building** — injects user profile, step data, and current goal into the system prompt
2. **LLM call** — sends conversation + tools to Claude via the Anthropic API
3. **Tool execution** — if the LLM calls a tool, executes it and feeds the result back
4. **Loop** — repeats until `stop_reason == "end_turn"` (max 10 iterations to prevent infinite loops)


### Tools

| Tool | Description |
|------|-------------|
| `calculate_calories` | MET-based calorie estimation from steps, adjusted for weight and height |
| `analyze_trends` | Identifies improving/declining/stable trends, streaks, weekly averages |
| `get_fitness_advice` | Tier-based personalized coaching tips based on % of goal achieved |
| `set_goal` | Sets a daily step or calorie goal |
| `check_goal_progress` | Tracks goal completion over the past 7 days |
| `parse_apple_health_csv` | Parses uploaded CSV files with date and steps columns |

---

## Deployment

### Backend (Render)

1. Push repo to GitHub
2. Go to https://render.com → New Web Service
3. Connect repo, set root to `backend/`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `ANTHROPIC_API_KEY`

### Frontend (Vercel)

1. Go to https://vercel.com → New Project → Import repo
2. Set root directory to `frontend/`
3. Framework: Vite
4. Update fetch URLs in `Chat.jsx` and `Setup.jsx` to point to your Render backend URL

---

## Tech Stack

- **Backend**: Python, FastAPI, Anthropic API (claude-opus-4-5)
- **Frontend**: React 18, Vite, Recharts, react-dropzone, react-markdown, Tailwind CSS
- **Fonts**: Syne (display), DM Sans (body), JetBrains Mono
