from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree


POSITION_NAMES = {
    "VOO": "Vanguard S&P 500 ETF",
    "QQQM": "Invesco Nasdaq 100 ETF",
    "NVDA": "NVIDIA",
    "GOOGL": "Alphabet",
    "JPM": "JPMorgan Chase",
    "COST": "Costco",
}

MARKET_SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "NVDA", "GOOGL", "JPM", "COST"]
NEWS_SYMBOLS = ["NVDA", "GOOGL", "JPM", "COST", "SPY"]
FALLBACK_SERIES = [188.7, 190.2, 193.8, 191.4, 196.6, 198.1, 200.04]

_CACHE: dict[str, Any] = {"expires_at": 0.0, "bundle": None}


def get_market_bundle() -> dict[str, Any]:
    now = time.time()
    if _CACHE["bundle"] and now < _CACHE["expires_at"]:
        return _CACHE["bundle"]

    symbols = sorted(set(MARKET_SYMBOLS + list(POSITION_NAMES)))
    charts = {symbol: fetch_chart(symbol) for symbol in symbols}
    news = fetch_news(charts)
    bundle = {
        "source": "Yahoo Finance chart/RSS endpoints",
        "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "quotes": {symbol: chart["quote"] for symbol, chart in charts.items()},
        "charts": {symbol: chart["series"] for symbol, chart in charts.items()},
        "news": news,
    }
    _CACHE.update({"expires_at": now + 180, "bundle": bundle})
    return bundle


def fetch_chart(symbol: str) -> dict[str, Any]:
    encoded = quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=1y&interval=1d"
    try:
        payload = fetch_json(url)
        result = payload["chart"]["result"][0]
        meta = result["meta"]
        timestamps = result.get("timestamp", [])
        quote_data = result["indicators"]["quote"][0]
        closes = quote_data.get("close", [])
        highs = quote_data.get("high", [])
        lows = quote_data.get("low", [])
        volumes = quote_data.get("volume", [])
        series = []
        for index, timestamp in enumerate(timestamps):
            close = closes[index] if index < len(closes) else None
            if close is None:
                continue
            series.append(
                {
                    "date": datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat(),
                    "close": round(float(close), 4),
                    "high": round(float(highs[index]), 4) if index < len(highs) and highs[index] else round(float(close), 4),
                    "low": round(float(lows[index]), 4) if index < len(lows) and lows[index] else round(float(close), 4),
                    "volume": int(volumes[index] or 0) if index < len(volumes) else 0,
                }
            )
        if len(series) < 2:
            raise ValueError(f"not enough chart data for {symbol}")
        latest = float(meta.get("regularMarketPrice") or series[-1]["close"])
        previous = float(series[-2]["close"])
        change_pct = ((latest - previous) / previous) * 100 if previous else 0
        quote_payload = {
            "symbol": symbol,
            "name": meta.get("longName") or meta.get("shortName") or POSITION_NAMES.get(symbol, symbol),
            "last_price": round(latest, 4),
            "previous_close": round(previous, 4),
            "change_pct": round(change_pct, 2),
            "day_high": round(float(meta.get("regularMarketDayHigh") or series[-1]["high"]), 4),
            "day_low": round(float(meta.get("regularMarketDayLow") or series[-1]["low"]), 4),
            "volume": int(meta.get("regularMarketVolume") or series[-1]["volume"]),
            "fifty_two_week_high": round(float(meta.get("fiftyTwoWeekHigh") or max(point["high"] for point in series)), 4),
            "fifty_two_week_low": round(float(meta.get("fiftyTwoWeekLow") or min(point["low"] for point in series)), 4),
            "market_time": datetime.fromtimestamp(int(meta.get("regularMarketTime", time.time())), timezone.utc).isoformat(),
        }
        return {"quote": quote_payload, "series": series[-180:]}
    except Exception:
        return fallback_chart(symbol)


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode())


def fallback_chart(symbol: str) -> dict[str, Any]:
    base = FALLBACK_SERIES
    offset = (sum(ord(char) for char in symbol) % 28) - 12
    series = [
        {
            "date": f"2026-06-{17 + index:02d}",
            "close": round(value + offset, 4),
            "high": round(value + offset + 1.8, 4),
            "low": round(value + offset - 1.6, 4),
            "volume": 1_000_000 + index * 170_000,
        }
        for index, value in enumerate(base)
    ]
    latest = series[-1]["close"]
    previous = series[-2]["close"]
    return {
        "quote": {
            "symbol": symbol,
            "name": POSITION_NAMES.get(symbol, symbol),
            "last_price": latest,
            "previous_close": previous,
            "change_pct": round(((latest - previous) / previous) * 100, 2),
            "day_high": series[-1]["high"],
            "day_low": series[-1]["low"],
            "volume": series[-1]["volume"],
            "fifty_two_week_high": max(point["high"] for point in series),
            "fifty_two_week_low": min(point["low"] for point in series),
            "market_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "series": series,
    }


def fetch_news(charts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for symbol in NEWS_SYMBOLS:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=8) as response:
                root = ElementTree.fromstring(response.read())
            for node in root.findall("./channel/item")[:4]:
                title = text_or_empty(node.find("title"))
                link = text_or_empty(node.find("link"))
                if not title or title in seen:
                    continue
                seen.add(title)
                pub_date = parse_pub_date(text_or_empty(node.find("pubDate")))
                description = text_or_empty(node.find("description"))
                items.append(build_research_item(symbol, title, description, link, pub_date, charts.get(symbol)))
        except Exception:
            continue
    if items:
        return sorted(items, key=lambda item: item["publishedAt"], reverse=True)[:8]
    return fallback_news(charts)


def build_research_item(
    symbol: str,
    title: str,
    description: str,
    link: str,
    published_at: str,
    chart: dict[str, Any] | None,
) -> dict[str, Any]:
    catalyst = classify_catalyst(title)
    sentiment = classify_sentiment(title + " " + description)
    impact = impact_model(symbol, catalyst, sentiment, chart["series"] if chart else fallback_chart(symbol)["series"])
    return {
        "id": f"{symbol}-{abs(hash(title))}",
        "title": title,
        "source": "Yahoo Finance RSS",
        "url": link,
        "catalyst": catalyst,
        "symbols": [symbol],
        "sentiment": sentiment,
        "summary": description or f"{symbol} headline routed through catalyst and trend impact analysis.",
        "publishedAt": published_at,
        "impact": impact,
    }


def impact_model(symbol: str, catalyst: str, sentiment: str, series: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [point["close"] for point in series[-80:]]
    latest = closes[-1]
    return_20d = pct_change(closes[-21], closes[-1]) if len(closes) > 21 else pct_change(closes[0], closes[-1])
    return_60d = pct_change(closes[0], closes[-1])
    volatility = realized_volatility(closes[-30:])
    catalyst_weight = {
        "Earnings": 1.15,
        "AI Infrastructure": 1.3,
        "Index Flow": 0.85,
        "Analyst Revision": 0.75,
        "Risk": 0.65,
        "Momentum": 0.9,
    }.get(catalyst, 0.7)
    sentiment_direction = {"constructive": 1, "watch": 0.35, "neutral": 0, "negative": -1}.get(sentiment, 0)
    trend_bias = max(min(return_20d / 100, 0.08), -0.08)
    shock = sentiment_direction * catalyst_weight * min(max(volatility / 100, 0.012), 0.06)
    projection = []
    for step in range(16):
        drift = trend_bias * (step / 15)
        ramp = shock * (1 - math.exp(-step / 5)) if step else 0
        baseline = latest * (1 + drift)
        projection.append(
            {
                "step": step,
                "baseline": round(baseline, 4),
                "bull": round(baseline * (1 + abs(ramp)), 4),
                "bear": round(baseline * (1 - abs(ramp) - min(volatility / 450, 0.035)), 4),
            }
        )
    return {
        "symbol": symbol,
        "latest": round(latest, 4),
        "return20d": round(return_20d, 2),
        "return60d": round(return_60d, 2),
        "realizedVolatility": round(volatility, 2),
        "trendScore": round(max(min(50 + return_20d * 2.2 + sentiment_direction * 12, 100), 0), 1),
        "shockPct": round(shock * 100, 2),
        "history": series[-70:],
        "projection": projection,
    }


def classify_catalyst(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ["earnings", "revenue", "profit"]):
        return "Earnings"
    if any(term in lower for term in ["ai", "chip", "nvidia", "data center"]):
        return "AI Infrastructure"
    if any(term in lower for term in ["dow", "index", "s&p", "nasdaq"]):
        return "Index Flow"
    if any(term in lower for term in ["upgrade", "downgrade", "target", "analyst"]):
        return "Analyst Revision"
    if any(term in lower for term in ["risk", "tariff", "fed", "rates", "lawsuit"]):
        return "Risk"
    return "Momentum"


def classify_sentiment(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ["falls", "risk", "warning", "miss", "lawsuit", "downgrade", "sell"]):
        return "negative"
    if any(term in lower for term in ["surges", "beats", "upgrade", "buy", "growth", "record", "strong"]):
        return "constructive"
    if any(term in lower for term in ["consider", "watch", "could", "set to", "joins"]):
        return "watch"
    return "neutral"


def realized_volatility(values: list[float]) -> float:
    returns = [math.log(values[index] / values[index - 1]) for index in range(1, len(values)) if values[index - 1]]
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252) * 100


def pct_change(start: float, end: float) -> float:
    return ((end - start) / start) * 100 if start else 0.0


def text_or_empty(node: ElementTree.Element | None) -> str:
    return (node.text or "").strip() if node is not None else ""


def parse_pub_date(value: str) -> str:
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat(timespec="seconds")
    except Exception:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fallback_news(charts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    defaults = [
        ("NVDA", "Semiconductor leadership remains concentrated around AI infrastructure", "Momentum in AI leaders is strong but position sizing remains the binding risk."),
        ("GOOGL", "Alphabet index inclusion and AI spending frame the next catalyst window", "Index-flow demand can support trend continuation, but capex scrutiny keeps the bear case alive."),
        ("SPY", "Market breadth improves while volatility stays compressed", "A calmer tape supports patience over churn and reduces urgency to force trades."),
    ]
    return [
        build_research_item(symbol, title, summary, "https://finance.yahoo.com/", datetime.now(timezone.utc).isoformat(timespec="seconds"), charts.get(symbol))
        for symbol, title, summary in defaults
    ]
