import os
import json
import asyncio
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

from marketpulse.storage.mongo_client import MongoStore
from marketpulse.graph.correlation_graph import (
    compute_correlation_matrix,
    get_similar_stocks,
    build_correlation_graph
)
from marketpulse.graph.community_detection import detect_stock_communities
from marketpulse.api.websocket import manager

app = FastAPI(title="MarketPulse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = MongoStore()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0", "storage": "mongo" if store.use_mongo else "local_fallback"}


@app.get("/api/tickers")
def get_tickers():
    prices = store.get_records("historical_prices", limit=5000)
    if not prices:
        from marketpulse.ingest.download_data import fetch_historical_daily
        df = fetch_historical_daily()
        prices = df.to_dict(orient="records")

    df = pd.DataFrame(prices)
    if df.empty:
        return []

    latest_per_ticker = []
    for ticker, group in df.groupby("Ticker"):
        g = group.sort_values(by="Date")
        last_row = g.iloc[-1]
        prev_close = g.iloc[-2]["Close"] if len(g) > 1 else last_row["Open"]
        change = round(((last_row["Close"] - prev_close) / prev_close) * 100, 2)
        latest_per_ticker.append({
            "ticker": str(ticker),
            "price": float(last_row["Close"]),
            "change_pct": change,
            "volume": float(last_row["Volume"]),
            "date": str(last_row["Date"])
        })
    return latest_per_ticker


@app.get("/api/prices/daily/{ticker}")
def get_daily_prices(ticker: str):
    ticker_clean = ticker.upper().replace(".NS", "")
    prices = store.get_records("historical_prices", query={"Ticker": ticker_clean}, limit=1000)
    if not prices:
        # Fallback query without filter if missing
        prices = [p for p in store.get_records("historical_prices", limit=5000) if p.get("Ticker") == ticker_clean]
    return prices


@app.get("/api/prices/minute/{ticker}")
def get_minute_prices(ticker: str):
    ticker_clean = ticker.upper().replace(".NS", "")
    min_path = os.path.join("data", "raw", "prices_minute.csv")
    if os.path.exists(min_path):
        df = pd.read_csv(min_path)
        g = df[df["Ticker"] == ticker_clean].tail(200)
        return g.to_dict(orient="records")
    return []


@app.get("/api/news")
def get_news():
    news = store.get_records("news", limit=100)
    if not news:
        news_path = os.path.join("data", "raw", "news_headlines.json")
        if os.path.exists(news_path):
            with open(news_path, "r", encoding="utf-8") as f:
                news = json.load(f)
    return news


@app.get("/api/metrics")
def get_metrics():
    metrics_path = os.path.join("reports", "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "logistic_regression": {"accuracy": 0.50, "precision": 0.50, "recall": 0.50, "f1": 0.50, "roc_auc": 0.50},
        "random_forest": {"accuracy": 0.52, "precision": 0.51, "recall": 0.53, "f1": 0.52, "roc_auc": 0.52},
        "lstm": {"accuracy": 0.51, "precision": 0.50, "recall": 0.51, "f1": 0.50, "roc_auc": 0.51}
    }


@app.get("/api/predictions")
def get_predictions(ticker: Optional[str] = None):
    query = {"ticker": ticker.upper()} if ticker else None
    preds = store.get_records("predictions", query=query, limit=200)
    return preds


@app.get("/api/graph/correlation")
def get_correlation_graph():
    daily_returns = store.get_records("daily_returns", limit=5000)
    if not daily_returns:
        proc_path = os.path.join("data", "processed", "daily_returns.csv")
        if os.path.exists(proc_path):
            df = pd.read_csv(proc_path)
        else:
            from marketpulse.spark_jobs.daily_returns import run_daily_returns_spark
            df = run_daily_returns_spark()
    else:
        df = pd.DataFrame(daily_returns)

    corr_matrix = compute_correlation_matrix(df)
    graph_data = build_correlation_graph(corr_matrix, threshold=0.25)
    return {
        "matrix": corr_matrix.to_dict(),
        "tickers": list(corr_matrix.columns),
        "graph": graph_data
    }


@app.get("/api/graph/similar/{ticker}")
def get_similar(ticker: str):
    ticker_clean = ticker.upper()
    proc_path = os.path.join("data", "processed", "daily_returns.csv")
    if os.path.exists(proc_path):
        df = pd.read_csv(proc_path)
    else:
        daily_returns = store.get_records("daily_returns", limit=5000)
        df = pd.DataFrame(daily_returns)

    corr_matrix = compute_correlation_matrix(df)
    similar = get_similar_stocks(ticker_clean, corr_matrix, top_n=4)
    return {"ticker": ticker_clean, "similar_stocks": similar}


@app.get("/api/graph/communities")
def get_communities():
    proc_path = os.path.join("data", "processed", "daily_returns.csv")
    if os.path.exists(proc_path):
        df = pd.read_csv(proc_path)
    else:
        daily_returns = store.get_records("daily_returns", limit=5000)
        df = pd.DataFrame(daily_returns)

    corr_matrix = compute_correlation_matrix(df)
    clusters = detect_stock_communities(corr_matrix)
    return {"communities": clusters}


@app.get("/api/streaming/stats")
def get_streaming_stats():
    return manager.consumer.get_summary()


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Poll simulator queue and send live ticks
            if not manager.simulator.output_queue.empty():
                tick = manager.simulator.output_queue.get()
                stats = manager.consumer.get_summary()
                payload = {"tick": tick, "stream_stats": stats}
                await websocket.send_json(payload)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
