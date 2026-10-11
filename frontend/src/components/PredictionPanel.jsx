import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, TrendingDown, Award } from 'lucide-react';

export default function PredictionPanel({ selectedTicker }) {
  const [metrics, setMetrics] = useState(null);
  const [predictions, setPredictions] = useState([]);

  useEffect(() => {
    fetch('/api/metrics')
      .then((res) => res.json())
      .then((data) => setMetrics(data))
      .catch(() => setMetrics(null));
  }, []);

  useEffect(() => {
    fetch(`/api/predictions?ticker=${selectedTicker}`)
      .then((res) => res.json())
      .then((data) => setPredictions(data || []))
      .catch(() => setPredictions([]));
  }, [selectedTicker]);

  const latestPred = predictions.length > 0 ? predictions[predictions.length - 1] : null;
  const isUp = latestPred?.predicted_direction === 'UP';

  return (
    <div className="bg-[#0F172A] border border-borderDark rounded-lg p-4 font-mono">
      <div className="border-b border-borderDark pb-2 mb-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Target className="w-4 h-4 text-emerald-400" />
          Direction Prediction & Model Evaluation
        </h3>
        <p className="text-xs text-slate-400">Short-term next-day direction (Walk-Forward Validation, No Data Leakage)</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {/* Signal Box */}
        <div className="bg-slate-900 border border-slate-800 p-3 rounded md:col-span-1">
          <span className="text-xs text-slate-400 block mb-1">Signal for {selectedTicker}:</span>
          {latestPred ? (
            <div>
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded font-bold text-sm mb-2 ${
                isUp ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-red-500/20 text-red-400 border border-red-500/40'
              }`}>
                {isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                PREDICTED {latestPred.predicted_direction}
              </div>
              <div className="text-xs text-slate-300">
                <span>Probability Up: </span>
                <span className="font-bold text-white">{(latestPred.probability_up * 100).toFixed(1)}%</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-2">Target date: {latestPred.date}</p>
            </div>
          ) : (
            <div className="text-xs text-slate-500 py-2">
              No active prediction signal for {selectedTicker}.
            </div>
          )}
        </div>

        {/* Models Walk-Forward Metrics Table */}
        <div className="bg-slate-900 border border-slate-800 p-3 rounded md:col-span-2 overflow-x-auto">
          <span className="text-xs text-slate-300 font-bold block mb-2 flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-amber-400" /> Walk-Forward Cross Validation Metrics
          </span>

          <table className="w-full text-left text-xs text-slate-300 font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                <th className="pb-1.5">Model</th>
                <th className="pb-1.5">Accuracy</th>
                <th className="pb-1.5">Precision</th>
                <th className="pb-1.5">Recall</th>
                <th className="pb-1.5">F1 Score</th>
                <th className="pb-1.5">ROC AUC</th>
              </tr>
            </thead>
            <tbody>
              {metrics && Object.entries(metrics).map(([name, m]) => (
                <tr key={name} className="border-b border-slate-800/50">
                  <td className="py-1.5 font-bold text-white uppercase">{name.replace('_', ' ')}</td>
                  <td className="py-1.5 text-emerald-400 font-bold">{(m.accuracy * 100).toFixed(1)}%</td>
                  <td className="py-1.5 font-mono">{(m.precision * 100).toFixed(1)}%</td>
                  <td className="py-1.5 font-mono">{(m.recall * 100).toFixed(1)}%</td>
                  <td className="py-1.5 font-mono">{(m.f1 * 100).toFixed(1)}%</td>
                  <td className="py-1.5 font-mono">{(m.roc_auc * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
