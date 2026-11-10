from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .models import SimulationRequest, StrategyUpdate
from .services import (
    economics_payload,
    latest_strategy,
    market_payload,
    portfolio_payload,
    research_payload,
    runs_payload,
    save_strategy,
    settings_payload,
    simulate_order,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    db.initialize_database()
    yield


app = FastAPI(
    title="Agentic Market Commander API",
    version="0.1.0",
    description="Local-first simulation API. No live trading endpoints are implemented.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "simulation"}


@app.get("/api/dashboard")
def dashboard() -> dict[str, object]:
    return {
        "portfolio": portfolio_payload(),
        "market": market_payload(),
        "strategy": latest_strategy(),
        "research": research_payload(),
        "economics": economics_payload(),
        "runs": runs_payload(),
    }


@app.get("/api/portfolio")
def portfolio() -> dict[str, object]:
    return portfolio_payload()


@app.get("/api/market")
def market() -> dict[str, object]:
    return market_payload()


@app.get("/api/strategy")
def strategy() -> dict[str, object]:
    return latest_strategy()


@app.post("/api/strategy")
def update_strategy(update: StrategyUpdate) -> dict[str, object]:
    return save_strategy(update)


@app.get("/api/research")
def research() -> dict[str, object]:
    return research_payload()


@app.get("/api/economics")
def economics() -> dict[str, object]:
    return economics_payload()


@app.get("/api/runs")
def runs() -> dict[str, object]:
    return runs_payload()


@app.get("/api/settings")
def settings() -> dict[str, str]:
    return settings_payload()


@app.post("/api/simulate/order")
def simulate(request: SimulationRequest) -> dict[str, object]:
    return simulate_order(request)
