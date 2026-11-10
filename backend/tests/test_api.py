from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_loads_seeded_data() -> None:
    with client:
        response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["portfolio"]["snapshot"]["total_value"] > 0
    assert len(data["portfolio"]["positions"]) == 6
    assert data["strategy"]["liveTradingAvailable"] is False


def test_strategy_rejects_live_trading() -> None:
    with client:
        current = client.get("/api/strategy").json()
        current["risk"]["liveTradingEnabled"] = True
        response = client.post(
            "/api/strategy",
            json={
                "name": "Unsafe change",
                "policyText": current["policyText"],
                "risk": current["risk"],
                "advanced": current["advanced"],
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert "Live trading cannot be enabled in v0.1." in body["errors"]


def test_simulation_blocks_oversized_trade() -> None:
    with client:
        response = client.post(
            "/api/simulate/order",
            json={"symbol": "NVDA", "action": "buy", "notionalUsd": 250},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["mode"] == "simulation-only"


def test_no_live_order_routes_are_registered() -> None:
    routes = {route.path for route in app.routes}
    forbidden = {
        "/api/orders",
        "/api/order",
        "/api/trades",
        "/api/broker/order",
        "/api/robinhood/order",
    }
    assert routes.isdisjoint(forbidden)
