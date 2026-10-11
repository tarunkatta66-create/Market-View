import React from 'react';
import { Activity, Database, AlertCircle } from 'lucide-react';

export default function Header({ isLiveConnected }) {
  return (
    <header className="border-b border-borderDark bg-[#0F172A] px-4 py-3">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="bg-emerald-500/10 text-emerald-400 p-2 rounded border border-emerald-500/20 font-mono font-bold tracking-wider">
            MP
          </div>
          <div>
            <h1 className="text-lg font-bold font-mono tracking-tight text-white flex items-center gap-2">
              MARKETPULSE <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-normal">CSC702 SEM-VII</span>
            </h1>
            <p className="text-xs text-slate-400 font-mono">Distributed Big Data Pipeline & Stock Direction Prediction</p>
          </div>
        </div>

        {/* Disclaimer Note */}
        <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 text-amber-400 px-3 py-1.5 rounded text-xs font-mono">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Educational project. Not financial advice.</span>
        </div>

        {/* Status Pills */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
            <Activity className={`w-3.5 h-3.5 ${isLiveConnected ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
            {isLiveConnected ? 'STREAM: LIVE' : 'STREAM: REPLAY'}
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
            <Database className="w-3.5 h-3.5 text-teal-400" />
            NOSQL: STORED
          </span>
        </div>
      </div>
    </header>
  );
}
