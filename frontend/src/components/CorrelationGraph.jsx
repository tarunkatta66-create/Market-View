import React, { useState, useEffect } from 'react';
import { GitGraph, Network, ArrowUpRight } from 'lucide-react';

export default function CorrelationGraph({ selectedTicker, onSelectTicker }) {
  const [similarStocks, setSimilarStocks] = useState([]);
  const [communities, setCommunities] = useState([]);
  const [graphData, setGraphData] = useState(null);

  useEffect(() => {
    if (selectedTicker) {
      fetch(`/api/graph/similar/${selectedTicker}`)
        .then((res) => res.json())
        .then((data) => setSimilarStocks(data.similar_stocks || []))
        .catch(() => setSimilarStocks([]));
    }
  }, [selectedTicker]);

  useEffect(() => {
    fetch('/api/graph/communities')
      .then((res) => res.json())
      .then((data) => setCommunities(data.communities || []))
      .catch(() => setCommunities([]));

    fetch('/api/graph/correlation')
      .then((res) => res.json())
      .then((data) => setGraphData(data.graph || null))
      .catch(() => setGraphData(null));
  }, []);

  return (
    <div className="bg-[#0F172A] border border-borderDark rounded-lg p-4 font-mono">
      <div className="border-b border-borderDark pb-2 mb-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <GitGraph className="w-4 h-4 text-accentAmber" />
          Module 5 Correlation Network & Recommendation Signal
        </h3>
        <p className="text-xs text-slate-400">Stock movement similarity and sector community clustering</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Similar Stocks Box */}
        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
            Stocks Correlated with {selectedTicker}
          </h4>
          <p className="text-[11px] text-slate-400 mb-3">Collaborative price movement similarity (Pearson r &ge; 0.3)</p>
          
          <div className="space-y-2">
            {similarStocks.map((sim) => (
              <div
                key={sim.ticker}
                onClick={() => onSelectTicker(sim.ticker)}
                className="flex items-center justify-between p-2 rounded bg-slate-800/80 border border-slate-700/60 hover:border-slate-500 cursor-pointer transition-colors text-xs"
              >
                <span className="font-bold text-white">{sim.ticker}</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 bg-slate-700 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-400 h-full rounded-full"
                      style={{ width: `${Math.max(0, sim.similarity * 100)}%` }}
                    />
                  </div>
                  <span className="text-emerald-400 font-bold">{sim.similarity}</span>
                </div>
              </div>
            ))}
            {similarStocks.length === 0 && (
              <span className="text-slate-500 text-xs italic">Select a ticker to view similarity signals...</span>
            )}
          </div>
        </div>

        {/* Sector Communities Box */}
        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <Network className="w-3.5 h-3.5 text-teal-400" />
            Graph Communities (Sector Clusters)
          </h4>
          <p className="text-[11px] text-slate-400 mb-3">Greedy modularity community detection on correlation graph</p>

          <div className="space-y-2">
            {communities.map((c) => (
              <div key={c.cluster_id} className="p-2 rounded bg-slate-800/60 border border-slate-700/50 text-xs">
                <div className="flex items-center justify-between text-slate-400 mb-1 font-semibold">
                  <span>Cluster #{c.cluster_id}</span>
                  <span className="text-[11px] text-teal-400">{c.count} Stocks</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {c.tickers.map((t) => (
                    <span
                      key={t}
                      onClick={() => onSelectTicker(t)}
                      className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-2 py-0.5 rounded text-[11px] font-bold cursor-pointer"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
            {communities.length === 0 && (
              <span className="text-slate-500 text-xs italic">Computing graph modularity clusters...</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
