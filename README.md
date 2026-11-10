# Agentic Market Commander

This simulation runs locally using SQLite. The public starting positions are manufactured whole-share examples. Runtime state stays outside Git.

A local-first stock-market command center for strategy control, research
visibility, API-cost economics, portfolio simulation, and deterministic demos.

> Version 0.1.0 is simulation-only. It has no live order endpoint, broker
> credential, or autonomous-trading path.

## How it works

- A FastAPI backend loads recent daily OHLCV and headline RSS data from Yahoo
  Finance endpoints.
- It recalculates simulated marks, day profit/loss, ticker signals, and projected
  research impact.
- Deterministic local fallback data keeps the interface usable when the feed is
  unavailable.
- A React/Vite frontend presents strategy, research, portfolio, and cost views.
- Local SQLite runtime state remains ignored and is not part of GitHub backup.

## Run locally

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Validate

```bash
cd backend
source .venv/bin/activate
pytest

cd ../frontend
npm run build
npm run lint
```

## Safety and data boundary

Do not add real brokerage credentials, account identifiers, portfolios, private
research, or paid data to this repository. A commercial or execution-enabled
milestone requires licensed data, authentication, auditability, explicit human
confirmation, loss/rate limits, a kill switch, compliance review, and sandboxed
acceptance.

Read [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for architecture, verified status,
hardening gaps, readiness assessment, backup policy, and cold-resume steps.
