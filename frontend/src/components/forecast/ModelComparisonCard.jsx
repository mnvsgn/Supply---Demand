import React from 'react';
import { Trophy, Layers, ShieldCheck, AlertCircle } from 'lucide-react';
import ModelComparisonTable from './ModelComparisonTable';
import { formatNumber, formatPercentage } from '../../utils/formatters';

export default function ModelComparisonCard({ evaluation }) {
  const selectedModel = evaluation?.selected_model_name || 'Winning Forecaster';
  const primaryMetric = evaluation?.primary_metric || 'wape';
  const metrics = evaluation?.validation_metrics || {};
  const period = evaluation?.validation_period || {};
  const warnings = evaluation?.warnings || [];

  return (
    <div className="rounded-2xl border border-slate-700/80 bg-slate-900/90 p-5 space-y-4 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Trophy className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Model Selection Benchmark
            </h3>
            <p className="text-xs text-slate-400">
              Evaluated on chronological out-of-sample window ({period.start || 'Start'} to {period.end || 'End'})
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-950 border border-emerald-800/40 text-emerald-300 font-medium">
            Winner: {selectedModel}
          </span>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">Validation WAPE</span>
          <span className="text-base font-bold font-mono text-emerald-400">
            {metrics.wape !== null && metrics.wape !== undefined ? formatPercentage(metrics.wape) : '—'}
          </span>
        </div>
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">Validation MAE</span>
          <span className="text-base font-bold font-mono text-slate-200">
            {metrics.mae !== null && metrics.mae !== undefined ? formatNumber(metrics.mae) : '—'}
          </span>
        </div>
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block">Validation RMSE</span>
          <span className="text-base font-bold font-mono text-slate-200">
            {metrics.rmse !== null && metrics.rmse !== undefined ? formatNumber(metrics.rmse) : '—'}
          </span>
        </div>
      </div>

      {/* Warnings if any */}
      {warnings.length > 0 && (
        <div className="rounded-lg bg-amber-950/20 border border-amber-800/30 p-2.5 text-xs text-amber-300/90 flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <span>{warnings.join(' ')}</span>
        </div>
      )}

      {/* Comparative Table */}
      <ModelComparisonTable
        comparison={evaluation?.comparison_table || []}
        primaryMetric={primaryMetric}
      />
    </div>
  );
}
