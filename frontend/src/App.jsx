import React, { useEffect, useState, useRef, useCallback } from "react";
import Header from "./components/Header";
import TickerBar from "./components/TickerBar";
import StockChart from "./components/StockChart";
import NewsPanel from "./components/NewsPanel";
import PredictionPanel from "./components/PredictionPanel";
import { ErrorBoundary } from "./components/ErrorBoundary";

// Normalizes API base URL: removes trailing slash if present, handles empty or relative setups
const rawApiUrl = import.meta.env.VITE_API_URL || "";
export const API_BASE = rawApiUrl ? rawApiUrl.replace(/\/+$/, "") : "";

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState("RELIANCE");
  const [tickers, setTickers] = useState([]);
  const [priceSeries, setPriceSeries] = useState([]);
  const [news, setNews] = useState([]);
  const [timeframe, setTimeframe] = useState("intraday");
  const [isWsConnected, setIsWsConnected] = useState(false);
  const [currentQuotes, setCurrentQuotes] = useState({});

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // 1. Initial Ticker list fetch
  useEffect(() => {
    let isMounted = true;
    fetch(`${API_BASE}/api/tickers`)
      .then((res) => {
        if (!res.ok) throw new Error("Network response was not ok");
        return res.json();
      })
      .then((data) => {
        if (!isMounted) return;
        if (Array.isArray(data) && data.length > 0) {
          setTickers(data);
          const quotesMap = {};
          data.forEach((t) => {
            const sym = (t.ticker || t.Ticker || "").replace(".NS", "");
            if (sym) quotesMap[sym] = t;
          });
          setCurrentQuotes((prev) => ({ ...prev, ...quotesMap }));
        }
      })
      .catch((err) => {
        console.warn("Could not fetch tickers from API:", err);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Fetch prices when selectedTicker or timeframe changes
  useEffect(() => {
    let isMounted = true;
    const cleanSym = selectedTicker.replace(".NS", "");
    const endpoint = timeframe === "daily"
      ? `${API_BASE}/api/prices/daily/${cleanSym}`
      : `${API_BASE}/api/prices?ticker=${cleanSym}`;

    fetch(endpoint)
      .then((res) => {
        if (!res.ok) throw new Error("Price fetch failed");
        return res.json();
      })
      .then((data) => {
        if (!isMounted) return;
        if (Array.isArray(data)) {
          setPriceSeries(data);
        } else {
          setPriceSeries([]);
        }
      })
      .catch((err) => {
        console.warn("Price series load note:", err);
        if (isMounted) setPriceSeries([]);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedTicker, timeframe]);

  // 3. Fetch News feed
  useEffect(() => {
    let isMounted = true;
    fetch(`${API_BASE}/api/news`)
      .then((res) => {
        if (!res.ok) throw new Error("News fetch failed");
        return res.json();
      })
      .then((data) => {
        if (!isMounted) return;
        if (Array.isArray(data)) {
          setNews(data);
        }
      })
      .catch((err) => {
        console.warn("News feed load note:", err);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // 4. WebSocket setup for live streaming price feeds
  const setupWebSocket = useCallback(() => {
    let wsUrl = "";
    if (API_BASE) {
      wsUrl = `${API_BASE.replace(/^http/, "ws")}/ws/stream`;
    } else {
      const loc = window.location;
      const proto = loc.protocol === "https:" ? "wss:" : "ws:";
      wsUrl = `${proto}//${loc.host}/ws/stream`;
    }

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const tick = payload.tick || payload;
          if (!tick || !tick.ticker) return;

          const tickSymbol = String(tick.ticker).replace(".NS", "");
          const cleanSelected = selectedTicker.replace(".NS", "");

          // Update real-time quote snapshot
          setCurrentQuotes((prev) => ({
            ...prev,
            [tickSymbol]: {
              ticker: tickSymbol,
              price: Number(tick.price ?? tick.Close ?? 0),
              change_pct: Number(tick.change_pct ?? 0),
              volume: Number(tick.volume ?? 0),
              timestamp: tick.timestamp || new Date().toLocaleTimeString()
            }
          }));

          // If this tick matches selectedTicker and we are in intraday mode, append to chart
          if (tickSymbol.toUpperCase() === cleanSelected.toUpperCase() && timeframe === "intraday") {
            setPriceSeries((prev) => {
              const safePrev = Array.isArray(prev) ? prev : [];
              const newPoint = {
                Timestamp: tick.timestamp || new Date().toISOString(),
                Ticker: tickSymbol,
                Close: Number(tick.price ?? 0),
                Open: Number(tick.open ?? tick.price ?? 0),
                High: Number(tick.high ?? tick.price ?? 0),
                Low: Number(tick.low ?? tick.price ?? 0),
                Volume: Number(tick.volume ?? 0)
              };
              const updated = [...safePrev, newPoint];
              return updated.length > 200 ? updated.slice(-200) : updated;
            });
          }
        } catch (e) {
          console.warn("WebSocket parse warning:", e);
        }
      };

      ws.onerror = () => {
        setIsWsConnected(false);
      };

      ws.onclose = () => {
        setIsWsConnected(false);
        // Auto-reconnect after 4s
        reconnectTimeoutRef.current = setTimeout(() => {
          setupWebSocket();
        }, 4000);
      };
    } catch (e) {
      console.warn("WebSocket connection failure:", e);
    }
  }, [selectedTicker, timeframe]);

  useEffect(() => {
    setupWebSocket();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [setupWebSocket]);

  const activeQuote = currentQuotes[selectedTicker.replace(".NS", "")] || null;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
        <Header isLive={isWsConnected} />

        {/* Ticker tape */}
        <TickerBar
          tickers={tickers}
          selectedTicker={selectedTicker}
          onSelectTicker={(sym) => setSelectedTicker(sym)}
        />

        {/* Main Content Dashboard */}
        <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Interactive Price Chart & AI Forecast */}
          <div className="lg:col-span-2 space-y-6">
            <StockChart
              ticker={selectedTicker}
              priceData={priceSeries}
              timeframe={timeframe}
              setTimeframe={setTimeframe}
              currentQuote={activeQuote}
            />

            <PredictionPanel
              selectedTicker={selectedTicker}
              apiBase={API_BASE}
            />
          </div>

          {/* Right Column: Financial News & LLM Sentiment */}
          <div className="lg:col-span-1">
            <NewsPanel news={news} />
          </div>
        </main>
      </div>
    </ErrorBoundary>
  );
}
