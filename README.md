# FitAgent 🏃 — AI-Powered Fitness Coach

FitAgent is an LLM-based agent that acts as your personal fitness coach. It analyzes your step data from Apple Health or Google Fit, calculates calories burned, identifies trends, and gives personalized advice — all through a conversational chat interface.

## Features

- **Agent loop written from scratch** — no LangChain, CrewAI, or other frameworks
- **7 tools** the agent can call: calorie calculator, trend analyzer, fitness advice engine, goal setter, goal progress tracker, Apple Health parser, Google Fit fetcher
- **Two data import methods**: Apple Health CSV/XML upload or Google Fit OAuth
- **React dashboard** with interactive charts (area chart, bar chart, stat cards)
- **Chat interface** to talk to the agent naturally
- **Full evaluation suite** with 25+ quantitative tests

---

## Project Structure

```
fitness-agent/
├── backend/
│   ├── agent.py          # Agent loop (planning + tool-calling)
│   ├── tools.py          # All 7 tool implementations
│   ├── main.py           # FastAPI server + endpoints
│   ├── requirements.txt
│   └── .env.example
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
│   ├── eval.py           # Evaluation suite
│   └── eval_results.json # Generated after running eval
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

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
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
2. **Import data**: Upload an Apple Health export CSV/XML, or connect Google Fit (see below)
3. **Dashboard**: View your step charts and stats
4. **Chat**: Ask FitAgent anything — it uses tools automatically

**Quick test with sample data**: Upload `data/samples/sample_steps.csv` on the Setup page.

---

## Google Fit Setup (Optional)

To enable Google Fit OAuth:

1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable the **Fitness API**
4. Go to **APIs & Services → Credentials → Create OAuth 2.0 Client ID**
5. Set Authorized redirect URI to: `http://localhost:8000/auth/google/callback`
6. Copy Client ID and Client Secret into your `.env` file

---

## Apple Health Export (iPhone)

1. Open the **Health** app
2. Tap your profile picture (top right)
3. Scroll down → **Export All Health Data**
4. Share/save the ZIP, unzip it, and upload `export.xml` or create a CSV

Alternatively, use the sample CSV at `data/samples/sample_steps.csv` to test.

---

## Running the Evaluation Suite

```bash
cd fitness-agent/eval
python eval.py
```

Results are printed to the console and saved to `eval/eval_results.json`.

The eval suite tests:
- **Calorie accuracy**: Validates against MET formula and Harvard reference values
- **Trend detection**: Tests improving/declining/stable classification
- **Advice quality**: Checks tier assignments and tip generation
- **Goal tracking**: Tests set/check goal flows
- **Parser robustness**: Tests CSV and XML parsing including edge cases

---

## Agent Design

The agent loop is in `backend/agent.py`:

1. **Context building** — injects user profile, step data, and current goal into the system prompt
2. **LLM call** — sends conversation + tools to Claude via the Anthropic API
3. **Tool execution** — if the LLM calls a tool, executes it and feeds the result back
4. **Loop** — repeats until `stop_reason == "end_turn"` (max 10 iterations)

No frameworks are used. The loop is ~60 lines of plain Python.

### Tools

| Tool | Description |
|------|-------------|
| `calculate_calories` | MET-based calorie estimation from steps |
| `analyze_trends` | Identifies improving/declining/stable trends, streaks, weekly averages |
| `get_fitness_advice` | Tier-based personalized coaching tips |
| `set_goal` | Sets a daily step or calorie goal |
| `check_goal_progress` | Tracks goal completion over the past 7 days |
| `parse_apple_health_csv` | Parses Apple Health XML export or CSV |
| `fetch_google_fit_steps` | Fetches steps from Google Fit REST API via OAuth |

---

## Deployment

### Deploy Backend (Render)

1. Push your repo to GitHub
2. Go to https://render.com → New Web Service
3. Connect your repo, set root to `backend/`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables: `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`

### Deploy Frontend (Vercel)

1. Go to https://vercel.com → New Project → Import your repo
2. Set root directory to `frontend/`
3. Framework: Vite
4. Update `vite.config.js` proxy to point to your Render backend URL

---

## Tech Stack

- **Backend**: Python, FastAPI, Anthropic API (claude-opus-4-5)
- **Frontend**: React 18, Vite, Recharts, react-dropzone, react-markdown, Tailwind CSS
- **Data sources**: Apple Health (XML/CSV export), Google Fit REST API
- **Fonts**: Syne (display), DM Sans (body), JetBrains Mono
