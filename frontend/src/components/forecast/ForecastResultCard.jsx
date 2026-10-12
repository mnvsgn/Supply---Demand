import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';
import {
  TrendingUp,
  Table as TableIcon,
  Trophy,
  Sliders,
  Sparkles,
  BarChart2,
  Calendar,
  AlertTriangle,
  RotateCw,
} from 'lucide-react';
import ForecastChart from './ForecastChart';
import ForecastTable from './ForecastTable';
import ModelComparisonTable from './ModelComparisonTable';
import { formatNumber, formatPercentage } from '../../utils/formatters';

export default function ForecastResultCard({ forecastResult }) {
  const { runForecast, isForecasting, sessionId, activeDataset } = useChat();
  const [activeTab, setActiveTab] = useState('chart'); // 'chart' | 'table' | 'models' | 'features'

  const forecastRows = forecastResult?.forecast || [];
  const modelName = forecastResult?.model_name || 'Forecast Engine';
  const horizon = forecastResult?.horizon || forecastRows.length;
  const frequency = forecastResult?.frequency || 'D';
  const metrics = forecastResult?.metrics || {};
  const modelComparison = forecastResult?.model_comparison || [];
  const featureImportance = forecastResult?.feature_importance || null;
  const warnings = forecastResult?.warnings || [];
  const recentHistory = forecastResult?.metadata?.recent_history || [];
  const targetProduct = forecastResult?.metadata?.product_id || activeDataset?.mapped_schema?.product_id || null;

  // Calculate summary metrics across the projected horizon
  const totalPredicted = forecastRows.reduce(
    (acc, cur) => acc + (cur.predicted_demand ?? cur.forecast ?? 0),
    0
  );
  const avgPredicted = forecastRows.length > 0 ? totalPredicted / forecastRows.length : 0;
  const peakPredicted = forecastRows.reduce(
    (max, cur) => Math.max(max, cur.predicted_demand ?? cur.forecast ?? 0),
    0
  );

  return (
    <div className="rounded-2xl border border-[#262626] bg-[#181818] p-5 space-y-5 shadow-sm">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#262626] pb-4">
        <div className="flex items-start space-x-3">
          <div className="p-2.5 rounded-xl bg-[#193228] text-emerald-400 border border-[#234b3c]">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-white tracking-tight">
                {modelName}
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#193228] text-emerald-400 border border-[#234b3c]">
                {horizon} Periods ({frequency})
              </span>
            </div>
            <p className="text-xs text-neutral-400 mt-0.5">
              Out-of-sample multi-step demand projection with 95% uncertainty intervals.
            </p>
          </div>
        </div>

        {/* Quick Horizon Buttons */}
        <div className="flex items-center space-x-1.5 self-start sm:self-auto">
          {[7, 14, 30].map((h) => (
            <button
              key={h}
              onClick={() => runForecast({ horizon: h, model_type: 'auto' })}
              disabled={isForecasting || horizon === h}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                horizon === h
                  ? 'bg-white text-black border-white'
                  : 'bg-[#222222] hover:bg-[#282828] text-neutral-300 border-[#2c2c2c] disabled:opacity-50'
              }`}
            >
              {h}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary KPI Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-[#141414] border border-[#262626]">
          <span className="text-[10px] uppercase font-semibold text-neutral-400 block">Total Forecasted</span>
          <span className="text-base sm:text-lg font-bold font-mono text-emerald-400">
            {formatNumber(totalPredicted, 0)}
          </span>
          <span className="text-[10px] text-neutral-500 block">across {horizon} periods</span>
        </div>

        <div className="p-3 rounded-xl bg-[#141414] border border-[#262626]">
          <span className="text-[10px] uppercase font-semibold text-neutral-400 block">Average Demand / Period</span>
          <span className="text-base sm:text-lg font-bold font-mono text-neutral-200">
            {formatNumber(avgPredicted, 1)}
          </span>
          <span className="text-[10px] text-neutral-500 block">expected daily run-rate</span>
        </div>

        <div className="p-3 rounded-xl bg-[#141414] border border-[#262626]">
          <span className="text-[10px] uppercase font-semibold text-neutral-400 block">Peak Demand Point</span>
          <span className="text-base sm:text-lg font-bold font-mono text-amber-400">
            {formatNumber(peakPredicted, 1)}
          </span>
          <span className="text-[10px] text-neutral-500 block">highest projected period</span>
        </div>

        <div className="p-3 rounded-xl bg-[#141414] border border-[#262626]">
          <span className="text-[10px] uppercase font-semibold text-neutral-400 block">Validation WAPE</span>
          <span className="text-base sm:text-lg font-bold font-mono text-emerald-400">
            {metrics.wape !== null && metrics.wape !== undefined
              ? formatPercentage(metrics.wape)
              : 'Baseline'}
          </span>
          <span className="text-[10px] text-neutral-500 block">weighted absolute error</span>
        </div>
      </div>

      {/* Warnings if any */}
      {warnings.length > 0 && (
        <div className="rounded-xl bg-amber-950/20 border border-amber-800/30 p-3 text-xs text-amber-300 flex items-start space-x-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold block">Forecast Engine Notices:</span>
            <ul className="list-disc list-inside text-[11px] text-amber-200/80">
              {warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* View Tabs */}
      <div className="border-b border-[#262626] flex items-center space-x-2 text-xs">
        <button
          onClick={() => setActiveTab('chart')}
          className={`flex items-center space-x-1.5 py-2 px-3 border-b-2 font-medium transition-colors cursor-pointer ${
            activeTab === 'chart'
              ? 'border-emerald-400 text-emerald-400'
              : 'border-transparent text-neutral-400 hover:text-neutral-200'
          }`}
        >
          <BarChart2 className="w-3.5 h-3.5" />
          <span>Trajectory Chart</span>
        </button>

        <button
          onClick={() => setActiveTab('table')}
          className={`flex items-center space-x-1.5 py-2 px-3 border-b-2 font-medium transition-colors cursor-pointer ${
            activeTab === 'table'
              ? 'border-emerald-400 text-emerald-400'
              : 'border-transparent text-neutral-400 hover:text-neutral-200'
          }`}
        >
          <TableIcon className="w-3.5 h-3.5" />
          <span>Forecast Table</span>
        </button>

        {modelComparison.length > 0 && (
          <button
            onClick={() => setActiveTab('models')}
            className={`flex items-center space-x-1.5 py-2 px-3 border-b-2 font-medium transition-colors cursor-pointer ${
              activeTab === 'models'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <Trophy className="w-3.5 h-3.5" />
            <span>Model Comparison</span>
          </button>
        )}

        {featureImportance && Object.keys(featureImportance).length > 0 && (
          <button
            onClick={() => setActiveTab('features')}
            className={`flex items-center space-x-1.5 py-2 px-3 border-b-2 font-medium transition-colors ${
              activeTab === 'features'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Feature Importance</span>
          </button>
        )}
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === 'chart' && (
          <ForecastChart
            forecastRows={forecastRows}
            recentHistory={recentHistory}
            modelName={modelName}
            frequency={frequency}
            targetProduct={targetProduct}
            horizon={horizon}
            units="Units"
          />
        )}

        {activeTab === 'table' && (
          <ForecastTable
            forecastRows={forecastRows}
            filename={`forecast_${modelName.toLowerCase().replace(/\s+/g, '_')}_${horizon}d.csv`}
            metadata={{
              sessionId,
              modelName,
              horizon,
              frequency,
              datasetName: activeDataset?.filename,
            }}
          />
        )}

        {activeTab === 'models' && (
          <ModelComparisonTable
            comparison={modelComparison}
            primaryMetric={forecastResult?.metadata?.selection_metric || 'wape'}
          />
        )}

        {activeTab === 'features' && featureImportance && (
          <div className="space-y-3 p-2">
            <span className="text-xs text-slate-400 block">
              Relative importance of calendar, lag, and rolling statistics engineered features:
            </span>
            <div className="space-y-2">
              {Object.entries(featureImportance)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([feat, score], idx) => (
                  <div key={idx} className="space-y-1 text-xs">
                    <div className="flex justify-between text-slate-300">
                      <span className="font-mono text-[11px]">{feat}</span>
                      <span className="font-mono text-slate-400">{(score * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.min(100, score * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
