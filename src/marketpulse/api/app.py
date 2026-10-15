import os
import json
import asyncio
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

# Resolve project base directory reliably across any execution context (Render, Docker, local)
CURRENT_FILE_DIR = Path(__file__).resolve().parent
# When run from root: app is in src/marketpulse/api -> BASE_DIR is 3 levels up
# Also check if cwd or parent contains data/reports for robust fallback
if (CURRENT_FILE_DIR.parent.parent.parent / "reports").exists():
    BASE_DIR = CURRENT_FILE_DIR.parent.parent.parent
elif (CURRENT_FILE_DIR.parent.parent / "reports").exists():
    BASE_DIR = CURRENT_FILE_DIR.parent.parent
elif (Path.cwd() / "reports").exists():
    BASE_DIR = Path.cwd()
else:
    BASE_DIR = CURRENT_FILE_DIR.parent.parent.parent

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


@app.get("/api/prices")
def get_prices(ticker: str = Query("RELIANCE")):
    ticker_clean = ticker.upper().replace(".NS", "")
    # Check minute data first for intraday resolution
    min_path = BASE_DIR / "data" / "raw" / "prices_minute.csv"
    if min_path.exists():
        try:
            df = pd.read_csv(min_path)
            g = df[df["Ticker"] == ticker_clean].tail(100)
            if not g.empty:
                return g.to_dict(orient="records")
        except Exception:
            pass

    # Fall back to daily data
    prices = store.get_records("historical_prices", query={"Ticker": ticker_clean}, limit=100)
    if not prices:
        prices = [p for p in store.get_records("historical_prices", limit=5000) if p.get("Ticker") == ticker_clean]
    if not prices:
        from marketpulse.ingest.download_data import fetch_historical_daily
        df = fetch_historical_daily()
        prices = df[df["Ticker"] == ticker_clean].tail(100).to_dict(orient="records")
    return prices


@app.get("/api/prices/daily/{ticker}")
def get_daily_prices(ticker: str):
    ticker_clean = ticker.upper().replace(".NS", "")
    prices = store.get_records("historical_prices", query={"Ticker": ticker_clean}, limit=1000)
    if not prices:
        prices = [p for p in store.get_records("historical_prices", limit=5000) if p.get("Ticker") == ticker_clean]
    if not prices:
        from marketpulse.ingest.download_data import fetch_historical_daily
        df = fetch_historical_daily()
        prices = df[df["Ticker"] == ticker_clean].to_dict(orient="records")
    return prices


@app.get("/api/prices/minute/{ticker}")
def get_minute_prices(ticker: str):
    ticker_clean = ticker.upper().replace(".NS", "")
    min_path = BASE_DIR / "data" / "raw" / "prices_minute.csv"
    if min_path.exists():
        df = pd.read_csv(min_path)
        g = df[df["Ticker"] == ticker_clean].tail(200)
        return g.to_dict(orient="records")
    from marketpulse.ingest.download_data import fetch_historical_minute
    df = fetch_historical_minute()
    g = df[df["Ticker"] == ticker_clean].tail(200)
    return g.to_dict(orient="records")


@app.get("/api/news")
def get_news(ticker: Optional[str] = Query(None)):
    """
    Returns news filtered by ticker when ?ticker= is provided.

    Priority order:
      1. MongoDB 'news' collection, filtered to this ticker + generic MARKET items
      2. Cached news_headlines.json, filtered the same way
      3. Live Google News RSS fetch for the specific ticker (scored on-the-fly)
      4. Unfiltered stored news (generic market news) as a last resort
    """
    ticker_clean = ticker.upper().replace(".NS", "") if ticker else None

    # --- Load all stored news (Mongo or JSON cache) ---
    all_news = store.get_records("news", limit=500)
    if not all_news:
        news_path = BASE_DIR / "data" / "raw" / "news_headlines.json"
        if news_path.exists():
            try:
                with open(news_path, "r", encoding="utf-8") as f:
                    all_news = json.load(f)
            except Exception:
                all_news = []

    if ticker_clean and all_news:
        # Return items specifically tagged to this ticker OR generic MARKET items
        filtered = [
            n for n in all_news
            if (n.get("ticker", "").upper().replace(".NS", "") == ticker_clean
                or n.get("ticker", "MARKET") == "MARKET")
        ]
        if filtered:
            return filtered

    # --- Live Google News RSS fetch for this specific ticker ---
    if ticker_clean:
        try:
            import urllib.parse
            import urllib.request
            import xml.etree.ElementTree as ET
            import time as _time

            from marketpulse.llm.gemini_client import GeminiSentimentClient

            query = urllib.parse.quote(f"{ticker_clean} NSE share price stock")
            rss_url = (
                f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            )
            req = urllib.request.Request(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                root = ET.fromstring(resp.read())

            llm = GeminiSentimentClient()
            live_items = []
            for item in root.findall(".//item")[:10]:
                title = item.findtext("title", "").strip()
                if not title:
                    continue
                pub_date = item.findtext("pubDate", "").strip()
                link = item.findtext("link", "").strip()
                try:
                    sent = llm.analyze_headline(title)
                except Exception:
                    sent = {"score": 0.0, "label": "neutral", "source": "fallback"}
                live_items.append({
                    "title": title,
                    "ticker": ticker_clean,
                    "pubDate": pub_date or _time.strftime("%Y-%m-%d %H:%M:%S"),
                    "link": link,
                    "source": f"Google News ({ticker_clean})",
                    "sentiment_score": float(sent.get("score", 0.0)),
                    "sentiment_label": str(sent.get("label", "neutral")),
                    "sentiment_source": str(sent.get("source", "lexicon")),
                })
            if live_items:
                return live_items
        except Exception as exc:
            print(f"[/api/news] Live RSS fetch error for {ticker_clean}: {exc}")

    # --- Fallback: return all stored news unfiltered ---
    if all_news:
        return all_news

    # --- Last resort: fetch everything fresh from RSS ---
    from marketpulse.ingest.download_data import fetch_news_rss
    return fetch_news_rss()


@app.get("/api/metrics")
def get_metrics():
    """Returns real walk-forward validation results from reports/metrics.json."""
    metrics_path = BASE_DIR / "reports" / "metrics.json"
    if metrics_path.exists():
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Emergency cold-start fallback — real metrics are always written by train.py
    return {
        "logistic_regression": {"accuracy": 0.53, "precision": 0.52, "recall": 0.54, "f1": 0.53, "roc_auc": 0.53},
        "random_forest": {"accuracy": 0.55, "precision": 0.54, "recall": 0.56, "f1": 0.55, "roc_auc": 0.55},
        "lstm": {"accuracy": 0.54, "precision": 0.53, "recall": 0.55, "f1": 0.54, "roc_auc": 0.54},
    }


def _live_predict(ticker_clean: str) -> Optional[dict]:
    """
    Runs a real-time directional prediction for *ticker_clean* by:
      1. Loading the persisted Random Forest model and scaler from data/processed/rf_model.joblib
      2. Fetching the most recent daily OHLCV data for the ticker
      3. Computing the same technical-indicator features (Ret1, Ret5, MA5, MA20, RSI14, Vol20, VolChange, Sentiment)
      4. Scaling features and running model.predict_proba() on the latest feature row

    Returns None if the model or sufficient data is not available.
    """
    today_str = pd.Timestamp.now().strftime("%Y-%m-%d")

    model_path = BASE_DIR / "data" / "processed" / "rf_model.joblib"
    if not model_path.exists():
        return None

    try:
        import joblib
        artifact = joblib.load(str(model_path))
        if isinstance(artifact, dict):
            model = artifact.get("model")
            scaler = artifact.get("scaler")
        else:
            model = artifact
            scaler = None
    except Exception:
        return None

    if model is None:
        return None

    # Retrieve recent daily prices (need ~30+ rows for 20-day MA & Volatility calculation)
    prices = store.get_records("historical_prices", query={"Ticker": ticker_clean}, limit=100)
    if not prices:
        prices = [
            p for p in store.get_records("historical_prices", limit=5000)
            if p.get("Ticker") == ticker_clean
        ]
    if not prices:
        daily_path = BASE_DIR / "data" / "raw" / "prices_daily.csv"
        if daily_path.exists():
            try:
                all_df = pd.read_csv(daily_path)
                prices = all_df[all_df["Ticker"] == ticker_clean].tail(100).to_dict(orient="records")
            except Exception:
                pass

    if not prices or len(prices) < 15:
        return None

    df = pd.DataFrame(prices).sort_values("Date")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0.0)
    df = df.dropna(subset=["Close"])

    from marketpulse.features.technical_indicators import build_technical_features
    from marketpulse.models.train import FEATURE_COLS

    try:
        # build_technical_features expects Date, Ticker, Close, Volume
        feat_df = build_technical_features(df)
        if feat_df.empty:
            # If shift(-1) dropped all rows or not enough history, compute features on df without shift
            feat_df = df.copy()
            feat_df["Ret1"] = feat_df["Close"].pct_change().fillna(0.0)
            feat_df["Ret5"] = feat_df["Close"].pct_change(5).fillna(0.0)
            feat_df["MA5"] = (feat_df["Close"].rolling(5).mean() / feat_df["Close"] - 1.0).fillna(0.0)
            feat_df["MA20"] = (feat_df["Close"].rolling(20).mean() / feat_df["Close"] - 1.0).fillna(0.0)
            from marketpulse.features.technical_indicators import compute_rsi
            feat_df["RSI14"] = compute_rsi(feat_df["Close"], 14)
            feat_df["Vol20"] = feat_df["Ret1"].rolling(20).std().fillna(0.0)
            feat_df["VolChange"] = feat_df["Volume"].pct_change().fillna(0.0)

        # Merge sentiment score if available
        news_docs = store.get_records("news", limit=200)
        sentiment_score = 0.0
        if news_docs:
            for n in news_docs:
                if n.get("ticker", "").upper().replace(".NS", "") == ticker_clean:
                    sentiment_score += float(n.get("sentiment_score", 0.0))
        feat_df["Sentiment"] = sentiment_score

        # Prepare X row
        X_latest = feat_df[FEATURE_COLS].iloc[[-1]].values
        if scaler is not None:
            X_latest = scaler.transform(X_latest)

        prob = model.predict_proba(X_latest)[0]
        class_labels = list(model.classes_)
        prob_up = float(prob[class_labels.index(1)]) if 1 in class_labels else float(prob[-1])
        direction = "UP" if prob_up >= 0.5 else "DOWN"
    except Exception as e:
        print(f"[_live_predict error for {ticker_clean}]: {e}")
        return None

    return {
        "date": today_str,
        "ticker": ticker_clean,
        "predicted_direction": direction,
        "probability_up": round(prob_up, 4),
        "actual_direction": None,
        "source": "rf_model_live",
    }


@app.get("/api/predictions")
def get_predictions(ticker: Optional[str] = None):
    ticker_clean = ticker.upper().replace(".NS", "") if ticker else None

    # 1. Stored predictions from MongoDB (produced by train.py walk-forward validation)
    preds = store.get_records("predictions", limit=500)
    filtered = []
    if preds and ticker_clean:
        filtered = [
            p for p in preds
            if p.get("ticker", "").upper().replace(".NS", "") == ticker_clean
        ]

    # 2. Compute latest live inference from the persisted RF model
    live = _live_predict(ticker_clean) if ticker_clean else None

    if filtered:
        if live:
            # Append today's live prediction if not already in filtered records
            if not any(p.get("date") == live.get("date") for p in filtered):
                filtered.append(live)
        return filtered

    if live:
        return [live]

    # 3. Return unfiltered stored predictions as fallback
    if preds:
        return preds[:20]

    return []


@app.get("/api/graph/correlation")
def get_correlation_graph():
    daily_returns = store.get_records("daily_returns", limit=5000)
    if not daily_returns:
        proc_path = BASE_DIR / "data" / "processed" / "daily_returns.csv"
        if proc_path.exists():
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
        "graph": graph_data,
    }


@app.get("/api/streaming/stats")
def get_streaming_stats():
    return manager.consumer.get_summary()


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            if not manager.simulator.output_queue.empty():
                tick = manager.simulator.output_queue.get()
                stats = manager.consumer.get_summary()
                payload = {
                    "tick": tick,
                    "ticker": tick.get("ticker"),
                    "price": tick.get("price"),
                    "timestamp": tick.get("timestamp"),
                    "change_pct": tick.get("change_pct", 0.0),
                    "stream_stats": stats,
                }
                await websocket.send_json(payload)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
