from __future__ import annotations

import difflib
import json
from datetime import datetime
from typing import Any

from . import db
from .market_data import get_market_bundle
from .models import StrategyUpdate, SimulationRequest


PROHIBITED_POLICY_TERMS = [
    "ignore hard gates",
    "bypass policy",
    "place live order",
    "disable human review",
    "use margin",
    "short sell",
]


def portfolio_payload() -> dict[str, Any]:
    snapshot = db.row("SELECT * FROM portfolio_snapshots ORDER BY id DESC LIMIT 1")
    positions = db.rows("SELECT * FROM positions ORDER BY (quantity * last_price) DESC")
    market = get_market_bundle()
    quotes = market["quotes"]
    enriched_positions = []
    for item in positions:
        quote = quotes.get(item["symbol"], {})
        last_price = float(quote.get("last_price", item["last_price"]))
        previous_close = float(quote.get("previous_close", item["last_price"]))
        enriched_positions.append(
            {
                **item,
                "name": quote.get("name", item["name"]),
                "last_price": last_price,
                "previous_close": previous_close,
                "day_change_pct": quote.get("change_pct", item["day_change_pct"]),
                "marketValue": round(item["quantity"] * last_price, 4),
                "dayPl": round(item["quantity"] * (last_price - previous_close), 4),
                "unrealizedPl": round(item["quantity"] * (last_price - item["average_cost"]), 4),
                "volume": quote.get("volume", 0),
                "fiftyTwoWeekHigh": quote.get("fifty_two_week_high", last_price),
                "fiftyTwoWeekLow": quote.get("fifty_two_week_low", last_price),
                "series": market["charts"].get(item["symbol"], []),
            }
        )
    total_cost = sum(item["quantity"] * item["average_cost"] for item in positions)
    total_market = sum(item["marketValue"] for item in enriched_positions)
    day_pl = sum(item["dayPl"] for item in enriched_positions)
    unrealized_pl = sum(item["unrealizedPl"] for item in enriched_positions)
    cash = float(snapshot["cash"])
    total_value = total_market + cash
    return {
        "snapshot": {
            **snapshot,
            "total_value": round(total_value, 4),
            "equity_value": round(total_market, 4),
            "day_pl": round(day_pl, 4),
            "unrealized_pl": round(unrealized_pl, 4),
            "updated_at": market["fetchedAt"],
            "source": market["source"],
        },
        "positions": sorted(enriched_positions, key=lambda item: item["marketValue"], reverse=True),
        "allocation": {
            "cashPct": round((cash / total_value) * 100, 2),
            "equityPct": round((total_market / total_value) * 100, 2),
            "costBasis": round(total_cost, 4),
            "marketValue": round(total_market, 4),
        },
    }


def market_payload() -> dict[str, Any]:
    market = get_market_bundle()
    tickers = [
        {
            **quote,
            "signal": signal_for_quote(quote),
            "series": market["charts"].get(symbol, []),
        }
        for symbol, quote in market["quotes"].items()
        if symbol in {"SPY", "QQQ", "IWM", "DIA", "NVDA", "GOOGL", "JPM", "COST"}
    ]
    advances = sum(1 for ticker in tickers if ticker["change_pct"] > 0)
    declines = sum(1 for ticker in tickers if ticker["change_pct"] < 0)
    return {
        "status": "live feed",
        "sessionDate": market["fetchedAt"][:10],
        "source": market["source"],
        "fetchedAt": market["fetchedAt"],
        "tickers": sorted(tickers, key=lambda item: item["symbol"]),
        "breadth": [
            {"label": "Advancers", "value": advances},
            {"label": "Decliners", "value": declines},
            {"label": "Flat", "value": max(len(tickers) - advances - declines, 0)},
        ],
        "sparkline": [point["close"] for point in market["charts"].get("SPY", [])[-42:]],
    }


def latest_strategy() -> dict[str, Any]:
    current = db.row("SELECT * FROM strategy_versions ORDER BY id DESC LIMIT 1")
    if not current:
        raise RuntimeError("strategy seed is missing")
    return {
        "id": current["id"],
        "name": current["name"],
        "policyText": current["policy_text"],
        "risk": json.loads(current["risk_json"]),
        "advanced": json.loads(current["advanced_json"]),
        "createdAt": current["created_at"],
        "liveTradingAvailable": False,
    }


def validate_strategy(update: StrategyUpdate) -> list[str]:
    errors: list[str] = []
    lower_policy = update.policyText.lower()
    for term in PROHIBITED_POLICY_TERMS:
        if term in lower_policy:
            errors.append(f"Policy cannot include '{term}'.")
    if update.risk.liveTradingEnabled:
        errors.append("Live trading cannot be enabled in v0.1.")
    if update.risk.allowOptions:
        errors.append("Options are disabled until broker support and policy gates are implemented.")
    total_weight = (
        update.advanced.momentumWeight
        + update.advanced.qualityWeight
        + update.advanced.valuationWeight
        + update.advanced.catalystWeight
    )
    if total_weight != 100:
        errors.append("Advanced strategy weights must total 100.")
    if update.risk.cashTargetPct < 15:
        errors.append("Cash target must stay at or above 15%.")
    return errors


def save_strategy(update: StrategyUpdate) -> dict[str, Any]:
    errors = validate_strategy(update)
    before = latest_strategy()
    diff = list(
        difflib.unified_diff(
            before["policyText"].splitlines(),
            update.policyText.splitlines(),
            fromfile=before["name"],
            tofile=update.name,
            lineterm="",
        )
    )
    if errors:
        return {"ok": False, "errors": errors, "diff": diff, "strategy": before}
    with db.connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO strategy_versions
            (name, policy_text, risk_json, advanced_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                update.name,
                update.policyText,
                json.dumps(update.risk.model_dump()),
                json.dumps(update.advanced.model_dump()),
                datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
        )
    return {"ok": True, "errors": [], "diff": diff, "strategy": {**update.model_dump(), "id": cursor.lastrowid}}


def research_payload() -> dict[str, Any]:
    market = get_market_bundle()
    live_items = market.get("news", [])
    if live_items:
        return {
            "items": live_items,
            "watchlist": ["SPY", "QQQ", "VOO", "QQQM", "NVDA", "GOOGL", "JPM", "COST"],
        }
    items = db.rows("SELECT * FROM research_items ORDER BY published_at DESC")
    return {
        "items": [
            {
                "id": item["id"],
                "title": item["title"],
                "source": item["source"],
                "url": item["url"],
                "catalyst": item["catalyst"],
                "symbols": json.loads(item["symbols_json"]),
                "sentiment": item["sentiment"],
                "summary": item["summary"],
                "publishedAt": item["published_at"],
                "impact": {},
            }
            for item in items
        ],
        "watchlist": ["SPY", "QQQ", "VOO", "QQQM", "NVDA", "GOOGL", "JPM", "COST"],
    }


def economics_payload() -> dict[str, Any]:
    costs = db.rows("SELECT * FROM api_costs ORDER BY created_at DESC")
    portfolio = portfolio_payload()["snapshot"]
    total_cost = sum(item["cost_usd"] for item in costs)
    expected_edge = max(abs(portfolio["day_pl"]), 0.01)
    justified = total_cost < expected_edge * 0.1
    by_agent: dict[str, float] = {}
    for item in costs:
        by_agent[item["agent"]] = round(by_agent.get(item["agent"], 0.0) + item["cost_usd"], 4)
    return {
        "totalCost": round(total_cost, 4),
        "costPctOfPortfolio": round((total_cost / portfolio["total_value"]) * 100, 4),
        "costPctOfDayPl": round((total_cost / expected_edge) * 100, 2),
        "isJustified": justified,
        "verdict": "Cost blocked" if not justified else "Cost acceptable",
        "byAgent": by_agent,
        "records": costs,
    }


def runs_payload() -> dict[str, Any]:
    return {
        "runs": db.rows("SELECT * FROM agent_runs ORDER BY id"),
        "safety": {
            "liveTrading": "disabled",
            "orderEndpoints": "not implemented",
            "killSwitch": "armed",
            "broker": "placeholder",
        },
    }


def settings_payload() -> dict[str, str]:
    return {row["key"]: row["value"] for row in db.rows("SELECT key, value FROM settings ORDER BY key")}


def simulate_order(request: SimulationRequest) -> dict[str, Any]:
    strategy = latest_strategy()
    errors = []
    if strategy["risk"]["liveTradingEnabled"]:
        errors.append("Unexpected live trading flag. Refusing simulation.")
    if request.action != "hold" and request.notionalUsd <= 0:
        errors.append("Buy and sell simulations require a notional amount.")
    if request.notionalUsd > 20:
        errors.append("Simulation blocks trade size above $20 for this account.")
    if request.action != "hold" and request.symbol.upper() not in settings_payload().get(
        "approved_symbols", "SPY,QQQ,VOO,QQQM,NVDA,GOOGL,JPM,COST"
    ):
        errors.append("Symbol is outside the approved mock universe.")
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "mode": "simulation-only",
        "request": request.model_dump(),
        "decision": "hold" if errors else f"simulated-{request.action}",
        "policyGate": "blocked" if errors else "pass",
    }


def signal_for_quote(quote: dict[str, Any]) -> str:
    change = float(quote.get("change_pct", 0))
    if change >= 1.0:
        return "breakout bid"
    if change >= 0.2:
        return "constructive"
    if change <= -1.0:
        return "risk-off"
    if change <= -0.2:
        return "pressure"
    return "balanced"
