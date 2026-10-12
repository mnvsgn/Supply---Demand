import React from 'react';
import { Trophy, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { formatNumber, formatPercentage } from '../../utils/formatters';

export default function ModelComparisonTable({ comparison = [], primaryMetric = 'wape' }) {
  if (!comparison || comparison.length === 0) {
    return (
      <div className="text-center py-6 text-slate-500 text-xs">
        No comparative model evaluation benchmarks available for this run.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-900/90 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="p-3">Model Candidate</th>
              <th className="p-3 text-center">Status</th>
              <th className="p-3 text-right">WAPE (%)</th>
              <th className="p-3 text-right">MAE</th>
              <th className="p-3 text-right">RMSE</th>
              <th className="p-3">Eligibility Note</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850 text-xs">
            {comparison.map((item, idx) => {
              const isBest = item.is_best || item.status === 'selected';
              const isEligible = item.is_eligible ?? true;
              const metrics = item.metrics || {};

              return (
                <tr
                  key={idx}
                  className={`transition-colors ${
                    isBest ? 'bg-blue-950/20 hover:bg-blue-950/30' : 'hover:bg-slate-900/40'
                  }`}
                >
                  <td className="p-3 font-medium text-slate-200">
                    <div className="flex items-center space-x-2">
                      {isBest && <Trophy className="w-4 h-4 text-amber-400 flex-shrink-0" />}
                      <span className={isBest ? 'text-blue-300 font-bold' : ''}>
                        {item.model_name || item.model_type}
                      </span>
                    </div>
                  </td>

                  <td className="p-3 text-center">
                    {isBest ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800/50">
                        Selected
                      </span>
                    ) : isEligible ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-800 text-slate-300">
                        Eligible
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-rose-950/50 text-rose-400 border border-rose-900/40">
                        Ineligible
                      </span>
                    )}
                  </td>

                  <td className="p-3 text-right font-mono font-medium text-slate-300">
                    {metrics.wape !== null && metrics.wape !== undefined
                      ? formatPercentage(metrics.wape)
                      : '—'}
                  </td>

                  <td className="p-3 text-right font-mono text-slate-400">
                    {metrics.mae !== null && metrics.mae !== undefined
                      ? formatNumber(metrics.mae)
                      : '—'}
                  </td>

                  <td className="p-3 text-right font-mono text-slate-400">
                    {metrics.rmse !== null && metrics.rmse !== undefined
                      ? formatNumber(metrics.rmse)
                      : '—'}
                  </td>

                  <td className="p-3 text-[11px] text-slate-400 max-w-xs truncate" title={item.eligibility_reason || 'Evaluated on backtest window'}>
                    {item.eligibility_reason || 'Evaluated on backtest window'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
