import pytest
from fastapi.testclient import TestClient
from marketpulse.api.app import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_api_tickers():
    res = client.get("/api/tickers")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_news():
    res = client.get("/api/news")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_metrics():
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "logistic_regression" in data
    assert "random_forest" in data


def test_api_correlation_graph():
    res = client.get("/api/graph/correlation")
    assert res.status_code == 200
    assert "graph" in res.json()


def test_api_streaming_stats():
    res = client.get("/api/streaming/stats")
    assert res.status_code == 200
    assert "bloom_filter_items_count" in res.json()
