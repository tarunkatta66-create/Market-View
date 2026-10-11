import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function TickerBar({ tickers, selectedTicker, onSelectTicker }) {
  if (!tickers || tickers.length === 0) {
    return (
      <div className="bg-[#0B0F17] border-b border-borderDark px-4 py-2 font-mono text-xs text-slate-500">
        Loading ticker feed...
      </div>
    );
  }

  return (
    <div className="bg-[#0B0F17] border-b border-borderDark px-4 py-2 overflow-x-auto">
      <div className="flex items-center gap-3 font-mono text-xs min-w-max">
        {tickers.map((t) => {
          const isUp = t.change_pct >= 0;
          const isSelected = selectedTicker === t.ticker;
          return (
            <button
              key={t.ticker}
              onClick={() => onSelectTicker(t.ticker)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded transition-all text-left ${
                isSelected
                  ? 'bg-slate-800 border border-slate-600 text-white shadow-sm'
                  : 'bg-slate-900/60 border border-slate-800 text-slate-300 hover:border-slate-700'
              }`}
            >
              <span className="font-bold tracking-tight">{t.ticker}</span>
              <span className="text-slate-400">₹{t.price ? t.price.toFixed(1) : '--'}</span>
              <span className={`flex items-center font-bold px-1.5 py-0.5 rounded text-[11px] ${
                isUp ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
              }`}>
                {isUp ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
                {isUp ? '+' : ''}{t.change_pct}%
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
