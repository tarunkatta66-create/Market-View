import os
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
import pandas as pd
import requests
from typing import List, Dict, Any
from marketpulse.storage.mongo_client import MongoStore
from marketpulse.llm.gemini_client import GeminiSentimentClient

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LTIM.NS", "TATAMOTORS.NS"
]

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://feeds.feedburner.com/ndtvprofit-latest"
]


def fetch_historical_daily(tickers: List[str] = TICKERS, period: str = "2y") -> pd.DataFrame:
    raw_dir = os.path.join("data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    all_data = []

    for ticker in tickers:
        try:
            import yfinance as yf
            df = yf.download(ticker, period=period, interval="1d", progress=False, session=session)
            if df is not None and not df.empty:
                df = df.reset_index()
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0] if c[1] == '' else c[0] for c in df.columns]

                df["Ticker"] = ticker.replace(".NS", "")
                df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
                
                for col in ["Open", "High", "Low", "Close", "Volume"]:
                    if col not in df.columns:
                        for alt in df.columns:
                            if col.lower() in alt.lower():
                                df[col] = df[alt]
                                break

                clean_df = df[["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]].dropna()
                if not clean_df.empty:
                    all_data.append(clean_df)
        except Exception as e:
            # Catch 404 Client Error, Cloud IP blocks, rate limits, etc.
            print(f"[Daily Ingest] Cloud/yfinance download note for {ticker} ({e}). Using synthetic generator.")

    if not all_data:
        all_data.append(_generate_synthetic_daily(tickers))

    combined = pd.concat(all_data, ignore_index=True)
    combined.to_csv(os.path.join(raw_dir, "prices_daily.csv"), index=False)
    return combined


def fetch_historical_minute(tickers: List[str] = TICKERS, period: str = "5d") -> pd.DataFrame:
    raw_dir = os.path.join("data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    all_data = []

    for ticker in tickers:
        try:
            import yfinance as yf
            df = yf.download(ticker, period=period, interval="5m", progress=False, session=session)
            if df is not None and not df.empty:
                df = df.reset_index()
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0] if c[1] == '' else c[0] for c in df.columns]

                date_col = "Datetime" if "Datetime" in df.columns else "Date"
                df["Timestamp"] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
                df["Ticker"] = ticker.replace(".NS", "")

                for col in ["Open", "High", "Low", "Close", "Volume"]:
                    if col not in df.columns:
                        for alt in df.columns:
                            if col.lower() in alt.lower():
                                df[col] = df[alt]
                                break

                clean_df = df[["Timestamp", "Ticker", "Open", "High", "Low", "Close", "Volume"]].dropna()
                if not clean_df.empty:
                    all_data.append(clean_df)
        except Exception as e:
            # Catch 404 Client Error, Cloud IP blocks, etc.
            print(f"[Minute Ingest] Cloud/yfinance download note for {ticker} ({e}). Using synthetic generator.")

    if not all_data:
        all_data.append(_generate_synthetic_minute(tickers))

    combined = pd.concat(all_data, ignore_index=True)
    combined.to_csv(os.path.join(raw_dir, "prices_minute.csv"), index=False)
    return combined


def fetch_news_rss(feeds: List[str] = RSS_FEEDS) -> List[Dict[str, Any]]:
    raw_dir = os.path.join("data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    items = []

    for feed_url in feeds:
        try:
            req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)

                for item in root.findall('.//item'):
                    title = item.findtext('title', '').strip()
                    pub_date = item.findtext('pubDate', '').strip()
                    link = item.findtext('link', '').strip()

                    if title:
                        items.append({
                            "title": title,
                            "pubDate": pub_date or time.strftime("%Y-%m-%d %H:%M:%S"),
                            "link": link,
                            "source": feed_url
                        })
        except Exception as e:
            print(f"RSS fetch warning for {feed_url}: {e}")

    if not items:
        items = _generate_synthetic_news()

    # Score news headlines with Gemini LLM client (with local VADER fallback)
    llm = GeminiSentimentClient()
    for item in items:
        try:
            sent = llm.analyze_headline(item["title"])
            item["sentiment_score"] = sent.get("score", 0.0)
            item["sentiment_label"] = sent.get("label", "neutral")
            item["sentiment_source"] = sent.get("source", "lexicon")
        except Exception:
            item["sentiment_score"] = 0.0
            item["sentiment_label"] = "neutral"
            item["sentiment_source"] = "fallback"

    with open(os.path.join(raw_dir, "news_headlines.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

    return items


def seed_mongodb(daily_df: pd.DataFrame, news_items: List[Dict[str, Any]]):
    store = MongoStore()
    
    daily_records = daily_df.to_dict(orient="records")
    store.clear_collection("historical_prices")
    store.insert_records("historical_prices", daily_records)

    store.clear_collection("news")
    store.insert_records("news", news_items)


def _generate_synthetic_daily(tickers: List[str]) -> pd.DataFrame:
    records = []
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='B')
    import numpy as np
    np.random.seed(42)

    for t in tickers:
        symbol = t.replace(".NS", "")
        price = 1000.0 if "RELIANCE" in symbol else (3000.0 if "TCS" in symbol else 500.0)
        for d in dates:
            change = np.random.normal(0.001, 0.015)
            close = round(price * (1 + change), 2)
            open_p = round(price, 2)
            high = round(max(open_p, close) * (1 + abs(np.random.normal(0, 0.005))), 2)
            low = round(min(open_p, close) * (1 - abs(np.random.normal(0, 0.005))), 2)
            vol = int(np.random.uniform(100000, 5000000))
            records.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Ticker": symbol,
                "Open": open_p,
                "High": high,
                "Low": low,
                "Close": close,
                "Volume": vol
            })
            price = close
    return pd.DataFrame(records)


def _generate_synthetic_minute(tickers: List[str]) -> pd.DataFrame:
    records = []
    times = pd.date_range(end=pd.Timestamp.now(), periods=200, freq='5min')
    import numpy as np
    np.random.seed(42)

    for t in tickers:
        symbol = t.replace(".NS", "")
        price = 1000.0 if "RELIANCE" in symbol else (3000.0 if "TCS" in symbol else 500.0)
        for tm in times:
            change = np.random.normal(0.0002, 0.003)
            close = round(price * (1 + change), 2)
            open_p = round(price, 2)
            high = round(max(price, close) + 0.5, 2)
            low = round(min(price, close) - 0.5, 2)
            records.append({
                "Timestamp": tm.strftime("%Y-%m-%d %H:%M:%S"),
                "Ticker": symbol,
                "Open": open_p,
                "High": high,
                "Low": low,
                "Close": close,
                "Volume": int(np.random.uniform(1000, 50000))
            })
            price = close
    return pd.DataFrame(records)


def _generate_synthetic_news() -> List[Dict[str, Any]]:
    return [
        {"title": "RBI keeps repo rate unchanged, market benchmark indices hit new highs", "pubDate": "2026-10-12 10:00:00", "link": "https://economictimes.indiatimes.com", "source": "Market News"},
        {"title": "TCS reports solid quarterly earnings with broad-based cloud momentum", "pubDate": "2026-10-12 11:30:00", "link": "https://moneycontrol.com", "source": "Market News"},
        {"title": "Reliance Industries expands green hydrogen capacity and retail footprint", "pubDate": "2026-10-12 12:15:00", "link": "https://economictimes.indiatimes.com", "source": "Market News"},
        {"title": "HDFC Bank notes strong credit deposit growth and improved asset quality", "pubDate": "2026-10-12 14:00:00", "link": "https://moneycontrol.com", "source": "Market News"},
        {"title": "IT and banking indices gain momentum amid positive foreign institutional inflows", "pubDate": "2026-10-12 15:10:00", "link": "https://ndtvprofit.com", "source": "Market News"},
    ]


if __name__ == "__main__":
    print("Downloading daily prices...")
    daily_df = fetch_historical_daily()
    print(f"Fetched {len(daily_df)} daily rows.")

    print("Downloading minute prices...")
    min_df = fetch_historical_minute()
    print(f"Fetched {len(min_df)} minute rows.")

    print("Fetching news feeds...")
    news = fetch_news_rss()
    print(f"Fetched {len(news)} news headlines.")

    print("Seeding MongoStore...")
    seed_mongodb(daily_df, news)
    print("Data download & seeding complete.")