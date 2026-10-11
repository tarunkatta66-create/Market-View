# Viva Presentation Notes

## Project Overview
- **Name**: MarketPulse
- **Goal**: End‑to‑end big‑data pipeline for stock market prediction.
- **Scope**: Academic prototype, disclaimer shown on UI.

## Dataset Characterisation (Module 1)
- Historical OHLCV data (minute & daily) for NIFTY‑50 constituents via **yfinance**.
- **Volume**: ~5 M rows of minute data (~2 GB CSV).
- **Velocity**: Simulated stream replays minute data at configurable speed (default 0.2 s per tick ≈ 5 ticks/sec).
- **Variety**: Structured price CSV, semi‑structured news JSON, unstructured headline text.
- Script `src/marketpulse/spark_jobs/dataset_stats.py` generates `dataset_stats.json` with concrete counts.

## Batch Processing (Module 2)
- **Spark job** `daily_returns.py` computes daily returns, moving averages, volatility; writes CSV and stores in MongoDB.
- **MapReduce job** `headline_wordcount_mapreduce.py` manually implements map‑reduce over news headlines; top‑100 words stored in MongoDB.
- Both jobs are invoked via `scripts/download_data.py` and can be run independently.

## Storage Design (Module 3)
- **MongoDB** collections:
  - `prices` – processed price records per ticker.
  - `news` – headline documents with cached sentiment.
  - `daily_returns`, `headline_wordcount` – batch job outputs.
- Document model fits mixed structured/unstructured data and enables quick retrieval for the API.

## Streaming Algorithms (Module 4)
- **Bloom Filter** – deduplicates incoming news headlines; exposes `count` for diagnostics.
- **DGIM** – maintains a sliding‑window count of up‑ticks per ticker.
- **Flajolet‑Martin** – estimates distinct active tickers in the current window.
- Unit tests compare against brute‑force baselines.

## Similarity & Clustering (Module 5)
- Correlation matrix calculated from historic returns.
- Graph of stocks where edges exist for correlation > 0.7.
- **Greedy modularity** detection (fallback to connected components) provides community clusters displayed on the dashboard.

## Prediction Component (Module 6)
- Features: technical indicators (MA, RSI, volatility, volume change) + news sentiment.
- Models trained with **walk‑forward validation** (expanding window) to respect time‑series ordering:
  - Logistic Regression (baseline)
  - Random Forest
  - LSTM (PyTorch, fallback to MLP)
- `reports/metrics.json` shows realistic accuracies (~0.50) and explains market efficiency limits.

## Results Summary (Refer to `reports/results_summary.md`)
- All models achieve 49‑51 % directional accuracy.
- Random Forest slightly outperforms LR; LSTM comparable.
- Feature importance: recent price movement and sentiment contribute most.
- Limitations: no order‑book data, simulated stream, limited horizon.

## Architecture Diagram
```
historical → Spark jobs → MongoDB → Feature store → Model training → FastAPI → React dashboard
                         ↑
                 streaming simulator → Bloom/DGIM/FM → MongoDB (features)
```

## viva_notes.md prepared for quick reference during the viva.

---
*All sections are concise to fit slide format.*
