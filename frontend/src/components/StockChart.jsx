import React, { useState } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function StockChart({ ticker, priceData, timeframe, setTimeframe }) {
  if (!priceData || priceData.length === 0) {
    return (
      <div className="bg-[#0F172A] border border-borderDark rounded-lg p-6 flex flex-col justify-center items-center h-80 font-mono text-sm text-slate-500">
        No price data available for {ticker}.
      </div>
    );
  }

  const latestPrice = priceData[priceData.length - 1]?.Close || priceData[priceData.length - 1]?.price || 0;
  const firstPrice = priceData[0]?.Close || priceData[0]?.open || latestPrice;
  const isOverallUp = latestPrice >= firstPrice;
  const strokeColor = isOverallUp ? '#10B981' : '#EF4444';
  const fillColor = isOverallUp ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';

  return (
    <div className="bg-[#0F172A] border border-borderDark rounded-lg p-4 font-mono">
      {/* Chart Header */}
      <div className="flex items-center justify-between border-b border-borderDark pb-3 mb-4">
        <div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-lg font-bold text-white tracking-wide">{ticker}</h2>
            <span className="text-xl font-bold text-slate-100">₹{Number(latestPrice).toFixed(2)}</span>
          </div>
          <p className="text-xs text-slate-400">Historical & Intraday Time Series (CSC702 Module 6 Analytics)</p>
        </div>

        {/* Timeframe Toggle Buttons */}
        <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded text-xs">
          <button
            onClick={() => setTimeframe('daily')}
            className={`px-3 py-1 rounded transition-colors ${
              timeframe === 'daily' ? 'bg-slate-700 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            DAILY (EOD)
          </button>
          <button
            onClick={() => setTimeframe('minute')}
            className={`px-3 py-1 rounded transition-colors ${
              timeframe === 'minute' ? 'bg-slate-700 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            5-MIN (STREAM)
          </button>
        </div>
      </div>

      {/* Recharts Area Container */}
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={priceData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={strokeColor} stopOpacity={0.4} />
                <stop offset="95%" stopColor={strokeColor} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis
              dataKey={timeframe === 'daily' ? 'Date' : 'Timestamp'}
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#1E293B' }}
              tickFormatter={(val) => (val ? String(val).slice(-5) : '')}
            />
            <YAxis
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(val) => `₹${val}`}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#0B0F17', borderColor: '#334155', borderRadius: '4px', fontSize: '12px' }}
              itemStyle={{ color: '#E2E8F0' }}
              formatter={(value) => [`₹${Number(value).toFixed(2)}`, 'Price']}
            />
            <Area
              type="monotone"
              dataKey={timeframe === 'daily' ? 'Close' : 'Close'}
              stroke={strokeColor}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPrice)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
