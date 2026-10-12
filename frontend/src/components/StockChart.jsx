import React, { useMemo } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { TrendingUp, TrendingDown, Clock } from 'lucide-react';

export default function StockChart({
  ticker = 'RELIANCE',
  priceData = [],
  timeframe = 'intraday',
  setTimeframe = () => {},
  currentQuote = null
}) {
  const cleanTicker = (ticker || 'RELIANCE').replace('.NS', '');

  // Normalize points safely
  const formattedData = useMemo(() => {
    if (!Array.isArray(priceData)) return [];
    return priceData
      .map((item, index) => {
        if (!item) return null;
        const val = Number(item.Close ?? item.price ?? item.ClosePrice ?? 0);
        const timeLabel = item.Timestamp || item.Date || item.timestamp || `T-${index}`;
        return {
          time: String(timeLabel),
          price: val,
        };
      })
      .filter((d) => d && d.price > 0);
  }, [priceData]);

  const latestPrice = useMemo(() => {
    if (currentQuote && currentQuote.price) return Number(currentQuote.price);
    if (formattedData.length > 0) return formattedData[formattedData.length - 1].price;
    return 0;
  }, [currentQuote, formattedData]);

  const firstPrice = useMemo(() => {
    if (formattedData.length > 0) return formattedData[0].price;
    return latestPrice;
  }, [formattedData, latestPrice]);

  const changePct = useMemo(() => {
    if (currentQuote && currentQuote.change_pct !== undefined) return Number(currentQuote.change_pct);
    if (firstPrice > 0 && latestPrice > 0) {
      return ((latestPrice - firstPrice) / firstPrice) * 100;
    }
    return 0;
  }, [currentQuote, firstPrice, latestPrice]);

  const isUp = changePct >= 0;
  const strokeColor = isUp ? '#059669' : '#e11d48'; // emerald-600 / rose-600
  const fillColor = isUp ? 'rgba(5, 150, 105, 0.08)' : 'rgba(225, 29, 72, 0.08)';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      {/* Top Header of Chart */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl font-bold text-slate-900">{cleanTicker}</h2>
            <span className="text-xs bg-slate-100 text-slate-600 font-medium px-2 py-0.5 rounded">
              NSE
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
              ₹{latestPrice > 0 ? latestPrice.toFixed(2) : '--'}
            </span>
            <span
              className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${
                isUp ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
              }`}
            >
              {isUp ? <TrendingUp className="w-3.5 h-3.5 mr-1" /> : <TrendingDown className="w-3.5 h-3.5 mr-1" />}
              {isUp ? '+' : ''}{changePct.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Timeframe switch */}
        <div className="flex items-center bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setTimeframe('intraday')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
              timeframe === 'intraday'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Intraday (Live)
          </button>
          <button
            onClick={() => setTimeframe('daily')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
              timeframe === 'daily'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Historical (Daily)
          </button>
        </div>
      </div>

      {/* Recharts Area Container */}
      <div className="h-80 w-full">
        {formattedData.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-sm gap-2">
            <Clock className="w-6 h-6 stroke-1 animate-spin text-slate-300" />
            <span>Streaming market chart data...</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={strokeColor} stopOpacity={0.25} />
                  <stop offset="95%" stopColor={strokeColor} stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="time"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                tickFormatter={(val) => {
                  if (!val) return '';
                  const parts = String(val).split(' ');
                  return parts.length > 1 ? parts[1].slice(0, 5) : String(val).slice(-5);
                }}
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                domain={['auto', 'auto']}
                tickFormatter={(val) => `₹${Number(val).toFixed(0)}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: '#e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
                  fontSize: '12px',
                  color: '#0f172a'
                }}
                formatter={(value) => [`₹${Number(value).toFixed(2)}`, 'Price']}
                labelFormatter={(label) => `Time: ${label}`}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke={strokeColor}
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#priceGradient)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
