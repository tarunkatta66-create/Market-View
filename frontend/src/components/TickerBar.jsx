import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function TickerBar({ tickers = [], selectedTicker = '', onSelectTicker = () => {} }) {
  if (!Array.isArray(tickers) || tickers.length === 0) {
    return (
      <div className="bg-white border-b border-slate-200 px-6 py-2.5 text-xs text-slate-400">
        Connecting to ticker streams...
      </div>
    );
  }

  return (
    <div className="bg-white border-b border-slate-200 px-4 sm:px-6 py-2 overflow-x-auto no-scrollbar">
      <div className="flex items-center gap-2 min-w-max">
        {tickers.map((t) => {
          if (!t) return null;
          const symbol = t.ticker || t.Ticker || 'UNKNOWN';
          const price = Number(t.price ?? t.Close ?? 0);
          const changePct = Number(t.change_pct ?? 0);
          const isUp = changePct >= 0;
          const isSelected = selectedTicker.toUpperCase().replace('.NS', '') === symbol.toUpperCase().replace('.NS', '');

          return (
            <button
              key={symbol}
              onClick={() => onSelectTicker(symbol)}
              className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg border text-xs transition-all ${
                isSelected
                  ? 'bg-slate-900 border-slate-900 text-white shadow-sm'
                  : 'bg-slate-50/70 border-slate-200 text-slate-700 hover:bg-slate-100 hover:border-slate-300'
              }`}
            >
              <span className="font-semibold">{symbol.replace('.NS', '')}</span>
              <span className={`font-medium ${isSelected ? 'text-slate-200' : 'text-slate-900'}`}>
                ₹{price > 0 ? price.toFixed(2) : '--'}
              </span>
              <span
                className={`inline-flex items-center font-semibold text-[11px] px-1.5 py-0.5 rounded ${
                  isSelected
                    ? isUp ? 'bg-emerald-500/30 text-emerald-300' : 'bg-rose-500/30 text-rose-300'
                    : isUp ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
                }`}
              >
                {isUp ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
                {isUp ? '+' : ''}{changePct.toFixed(2)}%
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
