# docs/decisions.md

# Architecture & Technical Decisions

- **Walk-Forward Time Series Validation**: Random k-fold cross-validation causes data leakage in time-series stock data. We use expanding-window walk-forward validation to ensure training only uses past information.
- **Direction Prediction over Exact Price Regression**: Predicting exact future stock prices overclaims signal quality and risks extreme overfitting. We formulate prediction as binary direction classification (up/down next-day close).
- **Simulated Stream via Python Queue**: Live WebSocket broker feeds require API credentials and paid market subscriptions. We stream replay minute-level historical data via a thread-safe queue to simulate a real-time feed.
- **Gemini Flash LLM with Local Fallback**: Gemini 3.5/3.6 Flash provides lightweight headline sentiment scoring. A local VADER/dictionary fallback ensures the pipeline runs 100% end-to-end without requiring active API keys.
- **Handcrafted Stream Algorithms**: Bloom Filter, DGIM algorithm, and Flajolet-Martin algorithm are implemented from scratch in pure Python to demonstrate Module 4 streaming theory without third-party library wrappers.
- **Flexible NoSQL Storage**: PyMongo connects to local MongoDB (`mongodb://localhost:27017`) when available, falling back to a local structured file system storage to guarantee zero-dependency execution.
