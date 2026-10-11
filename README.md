# MarketPulse

**MarketPulse** is an academic big‑data prototype that demonstrates a full end‑to‑end pipeline for short‑term stock‑price direction prediction. It combines historical OHLCV data, simulated real‑time price streams, and financial‑news sentiment, processes the data with PySpark and custom streaming algorithms, trains three machine‑learning models, and visualises the results in a dark‑themed React dashboard.

---

## Table of Contents
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Docker Compose](#docker-compose)
- [Modules Overview](#modules-overview)
- [Data Sources](#data-sources)
- [Prediction Models](#prediction-models)
- [Streaming Algorithms](#streaming-algorithms)
- [Documentation](#documentation)
- [Disclaimer](#disclaimer)

---

## Project Structure
```
MarketPulse/
├── data/                     # raw/ and processed/ (git‑ignored)
├── docs/                     # viva_notes.md, decisions.md
├── reports/                  # metrics.json, results_summary.md
├── src/marketpulse/
│   ├── ingest/               # download_data.py, ingest_news.py, stream_simulator.py
│   ├── streaming/            # bloom_filter.py, dgim.py, flajolet_martin.py, consumer.py
│   ├── spark_jobs/           # dataset_stats.py, daily_returns.py, headline_wordcount_mapreduce.py
│   ├── features/             # technical_indicators.py, sentiment.py
│   ├── graph/                # correlation_graph.py, community_detection.py
│   ├── models/               # train.py, evaluate.py, lstm_model.py
│   ├── llm/                  # gemini_client.py
│   └── api/                  # app.py, websocket.py, schemas.py
├── tests/                    # unit & integration tests
├── frontend/                 # React + Vite + Tailwind UI
├── Dockerfile.api
├── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
├── README.md                 # ← you are reading this file
└── scripts/                  # CLI wrappers (download_data.py, train.py)
```

---

## Setup
1. **Python environment** (Windows PowerShell)
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   The `requirements.txt` contains all needed packages (pandas, yfinance, pymongo, fastapi, uvicorn, pyspark, scikit‑learn, torch, vaderSentiment, etc.).

2. **MongoDB** (optional)
   - Install local MongoDB and start the service, or use the Docker‑Compose service (see below). The code falls back to a local file store if MongoDB is unavailable.

3. **Node.js** for the frontend
   ```powershell
   cd frontend
   npm install
   ```

---

## Running the Application
### 1. Download data (once)
```powershell
python scripts/download_data.py
```
   This pulls historical minute and daily OHLCV data from Yahoo Finance, fetches news headlines via RSS, scores sentiment (Gemini Flash if an API key is set, otherwise VADER), and seeds MongoDB.

### 2. Train models
```powershell
python scripts/train.py
```
   Generates `reports/metrics.json` and stores predictions in MongoDB.

### 3. Start the backend (FastAPI)
```powershell
uvicorn src.marketpulse.api.app:app --host 0.0.0.0 --port 8000
```
   The API is documented under `/docs` (Swagger UI).

### 4. Start the frontend (development mode)
```powershell
cd frontend
npm run dev
```
   Open <http://localhost:5173> in a browser. The dashboard connects to the backend via the Vite proxy.

---

## Docker Compose
A single command launches MongoDB, the API container, and the React UI:
```powershell
docker compose up --build
```
- API is exposed on **http://localhost:8000**.
- Frontend is served on **http://localhost** (Nginx). 
- MongoDB runs on the default port 27017 inside the network.

---

## Modules Overview
| Module | Purpose |
|--------|---------|
| **Ingestion** (`src/marketpulse/ingest`) | Pulls raw data, stores in `data/raw/`, seeds MongoDB. |
| **Batch Spark Jobs** (`src/marketpulse/spark_jobs`) | Computes daily returns, runs a manual MapReduce word‑count on news headlines. |
| **Streaming** (`src/marketpulse/streaming`) | Simulated price stream, Bloom filter for headline deduplication, DGIM for up‑tick counts, Flajolet‑Martin for distinct ticker estimate. |
| **Feature Engineering** (`src/marketpulse/features`) | Technical indicators (MA, RSI, volatility, volume change) + sentiment scores. |
| **Graph / Clustering** (`src/marketpulse/graph`) | Correlation matrix, similar‑stock retrieval, community detection (greedy modularity). |
| **Model Training** (`src/marketpulse/models`) | Walk‑forward validation, Logistic Regression, Random Forest, LSTM (PyTorch fallback). |
| **API** (`src/marketpulse/api`) | FastAPI routes for health, price data, news, streaming stats, predictions, graph data, and a WebSocket for live ticks. |
| **Frontend** (`frontend`) | React + Vite UI with Tailwind CSS, Recharts for charts, live diagnostics panel. |

---

## Data Sources
- **Historical OHLCV** – Yahoo Finance via `yfinance` (NIFTY‑50 tickers, e.g., `RELIANCE.NS`).
- **News** – Free RSS feeds (Moneycontrol, Economic Times). Headline sentiment scored by Gemini Flash wrapper; falls back to VADER if no API key.
- **Simulated Real‑Time** – `stream_simulator.py` replays minute‑level data through a Python `queue.Queue` at configurable speed.

---

## Prediction Models
- **Task** – Predict whether tomorrow’s closing price will be higher than today’s (binary direction).
- **Features** – Moving averages, RSI, volatility, volume change, and sentiment score.
- **Training** – Expanding‑window walk‑forward splits to avoid leakage.
- **Results** – See `reports/metrics.json` (accuracy ~0.49‑0.51). All models perform close to random, reflecting market efficiency.

---

## Streaming Algorithms
Implemented from scratch (no external libraries):
- **Bloom Filter** – Tracks inserted headlines; `count` exposed for UI diagnostics.
- **DGIM** – Approximate count of up‑ticks within a sliding window per ticker.
- **Flajolet‑Martin** – Estimates number of distinct active tickers.
Unit tests (`tests/test_*.py`) verify correctness against brute‑force baselines.

---

## Documentation
- **`docs/decisions.md`** – Design rationales (walk‑forward validation, simulated stream, LLM fallback, etc.).
- **`docs/viva_notes.md`** – Concise bullet points for viva presentation.
- **`reports/results_summary.md`** – Summary of model performance and key findings.
- API documentation available at `http://localhost:8000/docs` when the server is running.

---

## Disclaimer
> **Educational project. Not financial advice.**
The dashboard displays a visible disclaimer on every page. The models achieve only modest accuracy and should not be used for real trading decisions.

---

**Happy hacking!** If you encounter any issues, verify that MongoDB is running (or rely on the fallback) and that the required ports (8000 for API, 80 for UI) are free.
