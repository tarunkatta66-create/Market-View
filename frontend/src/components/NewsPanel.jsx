import React, { useState, useEffect } from 'react';
import { Newspaper, ExternalLink, Sparkles } from 'lucide-react';

export default function NewsPanel() {
  const [news, setNews] = useState([]);

  useEffect(() => {
    fetch('/api/news')
      .then((res) => res.json())
      .then((data) => setNews(data || []))
      .catch(() => setNews([]));
  }, []);

  return (
    <div className="bg-[#0F172A] border border-borderDark rounded-lg p-4 font-mono">
      <div className="border-b border-borderDark pb-2 mb-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-emerald-400" />
          Financial News & LLM Sentiment Pipeline
        </h3>
        <p className="text-xs text-slate-400">Gemini Flash LLM headline sentiment scoring & Bloom Filter deduplication</p>
      </div>

      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {news.map((item, idx) => {
          const score = item.sentiment_score || 0.0;
          const label = item.sentiment_label || 'neutral';
          const isPos = score > 0.05;
          const isNeg = score < -0.05;

          return (
            <div key={idx} className="bg-slate-900/90 border border-slate-800 p-2.5 rounded flex items-start justify-between gap-3 text-xs">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    isPos ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
                    isNeg ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                    'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}>
                    {label} ({score > 0 ? `+${score}` : score})
                  </span>
                  <span className="text-slate-500 text-[11px]">{item.pubDate}</span>
                  <span className="text-slate-500 text-[10px] flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-amber-400" /> {item.sentiment_source || 'llm'}
                  </span>
                </div>
                <a
                  href={item.link || '#'}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-slate-200 hover:text-white transition-colors flex items-center gap-1 group"
                >
                  {item.title}
                  <ExternalLink className="w-3 h-3 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                </a>
              </div>
            </div>
          );
        })}
        {news.length === 0 && (
          <div className="text-xs text-slate-500 italic py-4 text-center">
            Fetching RSS feeds and analyzing headline sentiment...
          </div>
        )}
      </div>
    </div>
  );
}
