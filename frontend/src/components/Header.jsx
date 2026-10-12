import React from "react";
import { Activity, ShieldCheck } from "lucide-react";

export default function Header({ isLive = false }) {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo & Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500 flex items-center justify-center text-white shadow-sm font-bold text-lg">
            M
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 text-lg tracking-tight">MarketPulse</span>
              <span className="bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase">
                Terminal
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Institutional-Grade Market Analytics & Forecasting</p>
          </div>
        </div>

        {/* Live Status & Disclaimer */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 px-2.5 py-1 rounded-full text-xs font-medium">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 ${isLive ? '' : 'hidden'}`}></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>{isLive ? "Live Stream Active" : "Connected"}</span>
          </div>

          <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-500 bg-slate-50 px-3 py-1 rounded-lg border border-slate-100">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
            <span>Educational project. Not financial advice.</span>
          </div>
        </div>
      </div>
    </header>
  );
}
