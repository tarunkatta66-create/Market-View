import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import TickerBar from './components/TickerBar';
import StockChart from './components/StockChart';
import StreamDiagnostics from './components/StreamDiagnostics';
import CorrelationGraph from './components/CorrelationGraph';
import PredictionPanel from './components/PredictionPanel';
import NewsPanel from './components/NewsPanel';

export default function App() {
  const [tickers, setTickers] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState('RELIANCE');
  const [priceData, setPriceData] = useState([]);
  const [timeframe, setTimeframe] = useState('daily');
  const [streamStats, setStreamStats] = useState(null);
  const [isLiveConnected, setIsLiveConnected] = useState(false);

  // Load initial tickers
  useEffect(() => {
    fetch('/api/tickers')
      .then((res) => res.json())
      .then((data) => {
        setTickers(data || []);
        if (data && data.length > 0) {
          setSelectedTicker(data[0].ticker);
        }
      })
      .catch(() => setTickers([]));
  }, []);

  // Load price data when selected ticker or timeframe changes
  useEffect(() => {
    if (!selectedTicker) return;

    const endpoint = timeframe === 'daily'
      ? `/api/prices/daily/${selectedTicker}`
      : `/api/prices/minute/${selectedTicker}`;

    fetch(endpoint)
      .then((res) => res.json())
      .then((data) => setPriceData(data || []))
      .catch(() => setPriceData([]));
  }, [selectedTicker, timeframe]);

  // Load initial stream stats
  useEffect(() => {
    fetch('/api/streaming/stats')
      .then((res) => res.json())
      .then((data) => setStreamStats(data))
      .catch(() => setStreamStats(null));
  }, []);

  // Connect to WebSocket stream endpoint
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/stream`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsLiveConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.stream_stats) {
          setStreamStats(payload.stream_stats);
        }
      } catch (e) {
        // ignore parse error
      }
    };

    ws.onclose = () => {
      setIsLiveConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col font-sans">
      <Header isLiveConnected={isLiveConnected} />
      <TickerBar tickers={tickers} selectedTicker={selectedTicker} onSelectTicker={setSelectedTicker} />

      <main className="flex-1 p-4 space-y-4 max-w-7xl w-full mx-auto">
        <StockChart
          ticker={selectedTicker}
          priceData={priceData}
          timeframe={timeframe}
          setTimeframe={setTimeframe}
        />

        <StreamDiagnostics stats={streamStats} />

        <PredictionPanel selectedTicker={selectedTicker} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CorrelationGraph selectedTicker={selectedTicker} onSelectTicker={setSelectedTicker} />
          <NewsPanel />
        </div>
      </main>

      <footer className="border-t border-borderDark bg-[#0F172A] px-4 py-3 text-center text-xs font-mono text-slate-500">
        MarketPulse CSC702 Course Project &bull; B.E. Computer Engineering &bull; Mumbai University R-2019 C-Scheme
      </footer>
    </div>
  );
}
