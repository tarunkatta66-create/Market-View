import React from 'react';
import { ShieldCheck, Cpu, Hash } from 'lucide-react';

export default function StreamDiagnostics({ stats }) {
  const bloomCount = stats?.bloom_filter_items_count || 0;
  const fmEstimate = stats?.distinct_tickers_estimated || 0;
  const processedTicks = stats?.processed_ticks_count || 0;
  const dgimCounts = stats?.dgim_uptick_counts || {};

  return (
    <div className="bg-[#0F172A] border border-borderDark rounded-lg p-4 font-mono">
      <div className="border-b border-borderDark pb-2 mb-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Cpu className="w-4 h-4 text-accentTeal" />
          Module 4 Stream Algorithm Diagnostics
        </h3>
        <p className="text-xs text-slate-400">Hand-coded algorithms running over live simulated stream</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
        {/* Bloom Filter Card */}
        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="flex items-center gap-1 font-bold text-slate-200">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> BLOOM FILTER
            </span>
            <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-emerald-400">DEDUP</span>
          </div>
          <div className="text-xl font-bold text-white">{bloomCount}</div>
          <p className="text-[11px] text-slate-400 mt-1">Deduplicated unique news headlines processed with ~1% FP bound.</p>
        </div>

        {/* DGIM Counter Card */}
        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="flex items-center gap-1 font-bold text-slate-200">
              <Cpu className="w-3.5 h-3.5 text-teal-400" /> DGIM COUNTER
            </span>
            <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-teal-400">SLIDING WINDOW</span>
          </div>
          <div className="text-xl font-bold text-white">{processedTicks}</div>
          <p className="text-[11px] text-slate-400 mt-1">Total ticks processed in sliding window (Logarithmic bucket sizes).</p>
        </div>

        {/* Flajolet-Martin Card */}
        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="flex items-center gap-1 font-bold text-slate-200">
              <Hash className="w-3.5 h-3.5 text-amber-400" /> FLAJOLET-MARTIN
            </span>
            <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-amber-400">DISTINCT EST</span>
          </div>
          <div className="text-xl font-bold text-white">{fmEstimate} <span className="text-xs text-slate-400 font-normal">tickers</span></div>
          <p className="text-[11px] text-slate-400 mt-1">Estimated active distinct stocks using trailing zeros hash estimator.</p>
        </div>
      </div>

      {/* DGIM Ticker Up-tick breakdown table */}
      <div className="bg-slate-900/50 border border-slate-800/80 rounded p-2 text-xs">
        <span className="text-slate-400 font-semibold mb-1 block">DGIM Window Up-Tick Events per Stock:</span>
        <div className="flex flex-wrap gap-2">
          {Object.entries(dgimCounts).map(([t, count]) => (
            <div key={t} className="bg-slate-800 px-2 py-1 rounded flex items-center gap-2">
              <span className="font-bold text-slate-200">{t}:</span>
              <span className="text-emerald-400 font-bold">{count} up-ticks</span>
            </div>
          ))}
          {Object.keys(dgimCounts).length === 0 && (
            <span className="text-slate-500 italic">Streaming ticks to compute DGIM window stats...</span>
          )}
        </div>
      </div>
    </div>
  );
}
