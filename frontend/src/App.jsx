import React, { useEffect, useState } from "react";
import TickerBar from "./components/TickerBar";
import StockChart from "./components/StockChart";
import NewsPanel from "./components/NewsPanel";
import PredictionPanel from "./components/PredictionPanel";
import Header from "./components/Header";

// Helper – builds full endpoint URL (adds trailing slash if missing)
const apiBase = (() => {
  const env = import.meta.env.VITE_API_URL || "http://localhost:8000";
  return env.endsWith("/") ? env.slice(0, -1) : env;
})();

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState("RELIANCE.NS");
  const [tickers, setTickers] = useState([]);
  const [priceSeries, setPriceSeries] = useState([]);
  const [news, setNews] = useState([]);

  // REST calls for initial data
  useEffect(() => {
    fetch(`${apiBase}/api/tickers`)
      .then((r) => r.json())
      .then(setTickers)
      .catch(() => setTickers([]));

    fetch(`${apiBase}/api/prices?ticker=${selectedTicker}`)
      .then((r) => r.json())
      .then(setPriceSeries)
      .catch(() => setPriceSeries([]));

    fetch(`${apiBase}/api/news`)
      .then((r) => r.json())
      .then(setNews)
      .catch(() => setNews([]));
  }, [selectedTicker]);

  // WebSocket for live price updates
  useEffect(() => {
    const ws = new WebSocket(`${apiBase.replace(/^http/, "ws")}/ws/stream`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPriceSeries((prev) => {
        const updated = [...prev, data];
        return updated.length > 200 ? updated.slice(-200) : updated;
      });
    };
    ws.onerror = () => console.error("WebSocket error");
    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      <Header />
      <main className="container mx-auto p-4 grid gap-4 lg:grid-cols-3">
        <section className="lg:col-span-1 space-y-4">
          <TickerBar tickers={tickers} selected={selectedTicker} onSelect={setSelectedTicker} />
          <NewsPanel news={news} />
        </section>
        <section className="lg:col-span-2 space-y-4">
          <StockChart data={priceSeries} ticker={selectedTicker} />
          <PredictionPanel selectedTicker={selectedTicker} />
        </section>
      </main>
    </div>
  );
}
