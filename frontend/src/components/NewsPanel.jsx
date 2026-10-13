import React from 'react';
import { Newspaper, ExternalLink, Sparkles } from 'lucide-react';

export default function NewsPanel({ news = [], selectedTicker = '' }) {
  const newsList = Array.isArray(news) ? news : [];
  const tickerLabel = selectedTicker ? selectedTicker.replace('.NS', '') : '';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
            <Newspaper className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              {tickerLabel ? `${tickerLabel} News & Sentiment` : 'Financial News & Sentiment'}
            </h3>
            <p className="text-xs text-slate-400">Real-time headlines analyzed with Gemini LLM</p>
          </div>
        </div>
        <span className="text-xs bg-slate-100 text-slate-600 font-medium px-2 py-0.5 rounded-full">
          {newsList.length} updates
        </span>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
        {newsList.map((item, idx) => {
          if (!item) return null;
          const score = Number(item.sentiment_score ?? 0);
          const label = item.sentiment_label || (score > 0.05 ? 'positive' : score < -0.05 ? 'negative' : 'neutral');
          const isPos = score > 0.05 || label.toLowerCase() === 'positive';
          const isNeg = score < -0.05 || label.toLowerCase() === 'negative';

          return (
            <div
              key={idx}
              className="p-3 rounded-lg border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                    isPos
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-150'
                      : isNeg
                      ? 'bg-rose-50 text-rose-700 border border-rose-150'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {label} {score !== 0 ? `(${score > 0 ? `+${score.toFixed(2)}` : score.toFixed(2)})` : ''}
                </span>

                <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                  <Sparkles className="w-3 h-3 text-amber-500" />
                  <span>{item.sentiment_source || 'AI sentiment'}</span>
                </div>
              </div>

              <a
                href={item.link && item.link !== '#' ? item.link : 'https://economictimes.indiatimes.com'}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-medium text-slate-800 hover:text-emerald-700 transition-colors line-clamp-2 block"
              >
                {item.title || 'Market intelligence update'}
              </a>

              {item.pubDate && (
                <span className="text-[10px] text-slate-400 block mt-1.5">
                  {item.pubDate}
                </span>
              )}
            </div>
          );
        })}

        {newsList.length === 0 && (
          <div className="text-center py-8 text-xs text-slate-400">
            Connecting to RSS financial news stream...
          </div>
        )}
      </div>
    </div>
  );
}
