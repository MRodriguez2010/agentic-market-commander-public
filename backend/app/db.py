from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "agentic_market_commander.sqlite3"


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY,
                total_value REAL NOT NULL,
                buying_power REAL NOT NULL,
                cash REAL NOT NULL,
                equity_value REAL NOT NULL,
                day_pl REAL NOT NULL,
                unrealized_pl REAL NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                quantity REAL NOT NULL,
                average_cost REAL NOT NULL,
                last_price REAL NOT NULL,
                day_change_pct REAL NOT NULL,
                thesis TEXT NOT NULL,
                risk TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tickers (
                symbol TEXT PRIMARY KEY,
                last_price REAL NOT NULL,
                change_pct REAL NOT NULL,
                signal TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS strategy_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                policy_text TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                advanced_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS research_items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                catalyst TEXT NOT NULL,
                symbols_json TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                summary TEXT NOT NULL,
                published_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS api_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                model TEXT NOT NULL,
                run_type TEXT NOT NULL,
                cost_usd REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY,
                lane TEXT NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                last_run TEXT NOT NULL,
                next_run TEXT NOT NULL,
                cost_usd REAL NOT NULL,
                decision TEXT NOT NULL,
                policy_gate TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        seed(conn)


def seed(conn: sqlite3.Connection) -> None:
    has_snapshot = conn.execute("SELECT COUNT(*) FROM portfolio_snapshots").fetchone()[0]
    if has_snapshot:
        return

    conn.execute(
        """
        INSERT INTO portfolio_snapshots
        (total_value, buying_power, cash, equity_value, day_pl, unrealized_pl, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (2635.0, 500.0, 500.0, 2135.0, 0.0, 0.0, "2026-06-23T15:45:00-05:00"),
    )

    # Fictional holdings for the local simulation.
    positions = [
        ('VOO', 'Example index position', 1, 500.0, 500.0, 0.0, 'Illustrative holding', 'Example'),
        ('QQQM', 'Example growth position', 2, 200.0, 200.0, 0.0, 'Illustrative holding', 'Example'),
        ('NVDA', 'Example semiconductor position', 3, 100.0, 100.0, 0.0, 'Illustrative holding', 'Example'),
        ('GOOGL', 'Example technology position', 2, 150.0, 150.0, 0.0, 'Illustrative holding', 'Example'),
        ('JPM', 'Example financial position', 1, 200.0, 200.0, 0.0, 'Illustrative holding', 'Example'),
        ('COST', 'Example retail position', 1, 435.0, 435.0, 0.0, 'Illustrative holding', 'Example'),
    ]
    conn.executemany(
        """
        INSERT INTO positions
        (symbol, name, quantity, average_cost, last_price, day_change_pct, thesis, risk)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        positions,
    )

    tickers = [
        ("SPY", 548.81, 0.16, "risk-on"),
        ("QQQ", 480.14, -0.08, "mixed breadth"),
        ("IWM", 205.39, 0.42, "small-cap bid"),
        ("VIX", 13.62, -2.14, "vol easing"),
        ("DXY", 104.11, 0.05, "flat dollar"),
        ("TNX", 4.31, -0.03, "yields stable"),
    ]
    conn.executemany("INSERT INTO tickers VALUES (?, ?, ?, ?)", tickers)

    risk = {
        "aggressiveness": 28,
        "maxPositionPct": 18,
        "maxDailyLossPct": 2.5,
        "cashTargetPct": 20,
        "allowOptions": False,
        "requireHumanReview": True,
        "liveTradingEnabled": False,
    }
    advanced = {
        "momentumWeight": 32,
        "qualityWeight": 28,
        "valuationWeight": 18,
        "catalystWeight": 22,
        "minimumScore": 74,
        "researchCadenceMinutes": 30,
        "rebalanceCadence": "daily-close",
        "primaryDecisionModel": "gpt-5.5",
        "researchModel": "gpt-5.4-mini",
        "heartbeatModel": "gpt-5.4-nano",
    }
    policy = """Mission: protect capital first, then compound through liquid US equities and ETFs.

Live trading remains disabled. Every recommendation is simulation-only until policy gates, broker review, and explicit human approval are implemented.

Hard gates:
- Keep at least 15% cash unless emergency liquidation is active.
- No options, margin, short selling, leveraged ETFs, crypto, or illiquid securities.
- No single position above 18% of portfolio value.
- Stop simulated trading for the day after a 2.5% drawdown.
- Reject any trade if source quality, quote freshness, or position sizing is uncertain.

Preferred setup:
- Favor broad market ETFs, profitable mega-cap compounders, and high-conviction catalysts.
- Avoid trading on unsourced news, social-only rumors, or stale price data.
- Minimize API cost when account size makes marginal intelligence uneconomical.
"""
    conn.execute(
        """
        INSERT INTO strategy_versions
        (name, policy_text, risk_json, advanced_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Default no-trade policy", policy, json.dumps(risk), json.dumps(advanced), "2026-06-23T15:50:00-05:00"),
    )

    research = [
        (
            "r1",
            "Semiconductor leaders hold relative strength as breadth narrows",
            "Mock Market Desk",
            "https://example.com/semiconductors",
            "Momentum",
            json.dumps(["NVDA", "QQQ"]),
            "constructive",
            "Leadership remains concentrated. The policy engine would require position-size discipline before adding exposure.",
            "2026-06-23T14:35:00-05:00",
        ),
        (
            "r2",
            "Mega-cap earnings revisions stay positive into the next reporting cycle",
            "Mock Earnings Monitor",
            "https://example.com/revisions",
            "Earnings",
            json.dumps(["GOOGL", "COST", "JPM"]),
            "watch",
            "Revision trend is supportive, but the portfolio is too small to justify frequent costly analysis runs.",
            "2026-06-23T13:20:00-05:00",
        ),
        (
            "r3",
            "Volatility compression supports patience over churn",
            "Mock Risk Tape",
            "https://example.com/volatility",
            "Risk",
            json.dumps(["SPY", "VIX"]),
            "neutral",
            "Low volatility reduces urgency. Simulation recommends holding current basket and preserving cash.",
            "2026-06-23T12:10:00-05:00",
        ),
    ]
    conn.executemany("INSERT INTO research_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", research)

    costs = [
        ("Strategy Council", "gpt-5.5", "decision-sim", 0.0312, "2026-06-23T14:00:00-05:00"),
        ("Research Desk", "gpt-5.4-mini", "catalyst-scan", 0.0064, "2026-06-23T14:30:00-05:00"),
        ("Heartbeat", "gpt-5.4-nano", "status-check", 0.0007, "2026-06-23T14:45:00-05:00"),
        ("EOD Analyst", "gpt-5.4-mini", "close-summary", 0.0098, "2026-06-22T16:05:00-05:00"),
    ]
    conn.executemany(
        "INSERT INTO api_costs (agent, model, run_type, cost_usd, created_at) VALUES (?, ?, ?, ?, ?)",
        costs,
    )

    runs = [
        ("run-research", "Research scan", "gpt-5.4-mini", "scheduled", "14:30", "15:00", 0.0064, "No catalyst strong enough to rebalance", "pass"),
        ("run-heartbeat", "Heartbeat", "gpt-5.4-nano", "healthy", "14:45", "14:50", 0.0007, "Market open, no drift alerts", "pass"),
        ("run-strategy", "Strategy council", "gpt-5.5", "blocked", "14:00", "15:30", 0.0312, "Hold. Cost exceeds expected edge for small account", "cost-block"),
        ("run-risk", "Risk governor", "rules-engine", "armed", "14:46", "continuous", 0.0, "Live order path unavailable in v0.1", "hard-block"),
    ]
    conn.executemany("INSERT INTO agent_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", runs)

    settings = [
        ("broker_connection", "Robinhood placeholder only"),
        ("trading_mode", "simulation"),
        ("storage_path", str(DB_PATH)),
        ("news_mode", "mock"),
    ]
    conn.executemany("INSERT INTO settings VALUES (?, ?)", settings)


def rows(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def row(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with connect() as conn:
        result = conn.execute(sql, params).fetchone()
        return dict(result) if result else None
