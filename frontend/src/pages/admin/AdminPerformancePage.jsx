import React, { useState, useEffect, useCallback } from 'react';
import AdminLayout from './AdminLayout';
import { useTheme } from '../../context/ThemeContext';
import { getModelPerformance } from '../../services/adminService';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import {
  LineChart,
  Cpu,
  TrendingUp,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';
import { formatInteger, formatDate, formatTime, formatPercentage } from '../../utils/formatters';

export default function AdminPerformancePage() {
  const { isDark } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getModelPerformance();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load performance metrics.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const secA = data?.training_and_testing;
  const secB = data?.operational_forecasts;
  const secC = data?.model_comparison;

  return (
    <AdminLayout currentTab="performance">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-white tracking-tight">
              Model Performance Telemetry
            </h1>
            <p className="text-xs text-neutral-400 mt-0.5">
              Empirical out-of-sample backtest errors, operational accuracy, and algorithm benchmarks.
            </p>
          </div>

          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#1a1a1a] hover:bg-[#222222] text-neutral-300 hover:text-white border border-[#2c2c2c] text-xs transition-colors cursor-pointer self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
            <span>Refresh Telemetry</span>
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-900/50 flex items-center space-x-2.5 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading && !data && (
          <div className="py-20 flex flex-col items-center justify-center space-y-3 text-neutral-400">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
            <span className="text-xs">Aggregating backtesting results and verification events...</span>
          </div>
        )}

        {data && (
          <>
            {/* ============================================================== */}
            {/* SECTION A: Training & Testing Performance                      */}
            {/* ============================================================== */}
            <section className="space-y-3">
              <div className="border-b border-[#212121] pb-2">
                <h2 className="text-sm font-semibold text-white tracking-tight flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-blue-400" />
                  <span>Section A: Training & Testing Performance</span>
                </h2>
                <p className="text-xs text-neutral-400 mt-0.5">
                  Out-of-sample error computed via chronological splits and rolling-origin backtests.
                </p>
              </div>

              {/* Summary Metrics Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-1">
                  <span className="text-xs text-neutral-400">Best Performing Model</span>
                  <div className="text-lg font-semibold text-white truncate">
                    {secA?.best_performing_model || 'Not evaluated'}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">Based on lowest WAPE error</span>
                </div>

                <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-1">
                  <span className="text-xs text-neutral-400">Last Evaluation Time</span>
                  <div className="text-sm font-medium text-neutral-200">
                    {secA?.last_evaluation_time ? formatDate(secA.last_evaluation_time) : '—'}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">
                    {secA?.last_evaluation_time ? formatTime(secA.last_evaluation_time) : 'No runs executed'}
                  </span>
                </div>

                <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-1">
                  <span className="text-xs text-neutral-400">Evaluated Series</span>
                  <div className="text-xl font-bold font-mono text-white">
                    {formatInteger(secA?.evaluated_series_count || 0)}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">Total backtest iterations</span>
                </div>

                <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-1">
                  <span className="text-xs text-neutral-400">Training Runs</span>
                  <div className="text-xl font-bold font-mono text-white">
                    {formatInteger(secA?.training_runs_count || 0)}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">Total model fits</span>
                </div>
              </div>

              {/* Candidate Models Comparison Table */}
              <div className="rounded-xl border border-[#262626] bg-[#161616] overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-[#1a1a1a] border-b border-[#262626] text-neutral-400 font-medium text-[11px]">
                        <th className="p-3">Model Architecture</th>
                        <th className="p-3">Evaluation Status</th>
                        <th className="p-3 text-right">MAE</th>
                        <th className="p-3 text-right">RMSE</th>
                        <th className="p-3 text-right">WAPE</th>
                        <th className="p-3">Last Evaluated</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#222222] font-mono text-xs text-neutral-300">
                      {secA?.candidate_models?.map((cand) => {
                        const hasMetrics = cand.status === 'evaluated' || cand.status === 'trained';
                        return (
                          <tr key={cand.key} className="hover:bg-[#1a1a1a] transition-colors">
                            <td className="p-3 font-sans font-medium text-neutral-200">
                              {cand.name}
                            </td>
                            <td className="p-3">
                              <span
                                className={`text-[10px] px-2 py-0.5 rounded border uppercase font-mono ${
                                  hasMetrics
                                    ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/40'
                                    : 'bg-neutral-800/60 text-neutral-400 border-neutral-700'
                                }`}
                              >
                                {cand.status === 'not_evaluated' ? 'Not evaluated' : cand.status}
                              </span>
                            </td>
                            <td className="p-3 text-right">
                              {cand.mae !== null && cand.mae !== undefined ? cand.mae.toFixed(2) : '—'}
                            </td>
                            <td className="p-3 text-right">
                              {cand.rmse !== null && cand.rmse !== undefined ? cand.rmse.toFixed(2) : '—'}
                            </td>
                            <td className="p-3 text-right font-semibold text-emerald-400">
                              {cand.wape !== null && cand.wape !== undefined ? formatPercentage(cand.wape) : '—'}
                            </td>
                            <td className="p-3 font-sans text-neutral-500">
                              {cand.last_evaluated ? `${formatDate(cand.last_evaluated)} ${formatTime(cand.last_evaluated)}` : '—'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            {/* ============================================================== */}
            {/* SECTION B: Operational Forecast Performance                    */}
            {/* ============================================================== */}
            <section className="space-y-3 pt-4">
              <div className="border-b border-[#212121] pb-2">
                <h2 className="text-sm font-semibold text-white tracking-tight flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  <span>Section B: Operational Forecast Performance</span>
                </h2>
                <p className="text-xs text-neutral-400 mt-0.5">
                  Accuracy measured strictly against verified ground-truth observations.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-1">
                  <span className="text-xs text-neutral-400">Forecasts Generated</span>
                  <div className="text-xl font-bold font-mono text-white">
                    {formatInteger(secB?.forecasts_generated || 0)}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">Across user sessions</span>
                </div>

                <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-1">
                  <span className="text-xs text-neutral-400">Verified Against Actuals</span>
                  <div className="text-xl font-bold font-mono text-white">
                    {formatInteger(secB?.forecasts_evaluated || 0)}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">Ground-truth verified</span>
                </div>

                <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-1">
                  <span className="text-xs text-neutral-400">Operational WAPE</span>
                  <div className="text-xl font-bold font-mono text-emerald-400">
                    {secB?.has_operational_evaluations && secB.wape !== null
                      ? formatPercentage(secB.wape)
                      : '—'}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">
                    {secB?.has_operational_evaluations ? 'Empirical accuracy' : 'Not evaluated'}
                  </span>
                </div>

                <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-1">
                  <span className="text-xs text-neutral-400">Last Forecast Timestamp</span>
                  <div className="text-sm font-medium text-neutral-200">
                    {secB?.last_forecast_timestamp ? formatDate(secB.last_forecast_timestamp) : '—'}
                  </div>
                  <span className="text-[11px] text-neutral-500 block">
                    {secB?.last_forecast_timestamp ? formatTime(secB.last_forecast_timestamp) : 'No forecasts yet'}
                  </span>
                </div>
              </div>
            </section>

            {/* ============================================================== */}
            {/* SECTION C: Model Comparison                                    */}
            {/* ============================================================== */}
            <section className="space-y-3 pt-4">
              <div className="border-b border-[#212121] pb-2">
                <h2 className="text-sm font-semibold text-white tracking-tight flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span>Section C: Model Comparison</span>
                </h2>
                <p className="text-xs text-neutral-400 mt-0.5">
                  Direct benchmark comparing Seasonal Naive, Random Forest, and XGBoost.
                </p>
              </div>

              {!secC?.has_data ? (
                <div className="rounded-xl border border-dashed border-[#262626] bg-[#161616] p-10 text-center space-y-2">
                  <Cpu className="w-8 h-8 text-neutral-600 mx-auto" />
                  <div className="text-sm font-medium text-neutral-300">
                    No Comparison Data Available
                  </div>
                  <p className="text-xs text-neutral-500 max-w-md mx-auto">
                    Execute an evaluation or forecast with automated model selection in the chat workspace
                    to populate comparative backtest charts and metrics.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Chart */}
                  <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-3">
                    <span className="text-xs font-semibold text-neutral-300">
                      Weighted Absolute Percentage Error (WAPE %)
                    </span>
                    <div className="h-56 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={secC.comparison_table}
                          margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
                        >
                          <CartesianGrid
                            strokeDasharray="3 3"
                            stroke={isDark ? '#262626' : '#e2e8f0'}
                            vertical={false}
                          />
                          <XAxis
                            dataKey="model_name"
                            stroke={isDark ? '#737373' : '#64748b'}
                            fontSize={11}
                            tickLine={false}
                          />
                          <YAxis
                            stroke={isDark ? '#737373' : '#64748b'}
                            fontSize={11}
                            tickLine={false}
                            unit="%"
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: isDark ? '#1c1c1c' : '#ffffff',
                              borderColor: isDark ? '#333333' : '#e2e8f0',
                              borderRadius: '8px',
                              fontSize: '12px',
                              color: isDark ? '#fff' : '#0f172a',
                            }}
                          />
                          <Bar dataKey="wape_pct" radius={[4, 4, 0, 0]} fill="#10b981" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Comparison Table */}
                  <div className="rounded-xl border border-[#262626] bg-[#161616] overflow-hidden">
                    <div className="p-3 border-b border-[#222222] text-xs font-semibold text-neutral-300">
                      Evaluated Comparison Table
                    </div>
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-[#1a1a1a] border-b border-[#262626] text-neutral-400 font-medium text-[11px]">
                          <th className="p-3">Model</th>
                          <th className="p-3 text-right">WAPE (%)</th>
                          <th className="p-3 text-right">MAE</th>
                          <th className="p-3 text-right">RMSE</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#222222] font-mono text-xs">
                        {secC.comparison_table.map((row, idx) => (
                          <tr key={idx} className="hover:bg-[#1a1a1a]">
                            <td className="p-3 font-sans font-medium text-neutral-200">
                              {row.model_name}
                            </td>
                            <td className="p-3 text-right font-semibold text-emerald-400">
                              {row.wape_pct !== null ? `${row.wape_pct}%` : '—'}
                            </td>
                            <td className="p-3 text-right text-neutral-300">
                              {row.mae !== null ? row.mae.toFixed(2) : '—'}
                            </td>
                            <td className="p-3 text-right text-neutral-300">
                              {row.rmse !== null ? row.rmse.toFixed(2) : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </AdminLayout>
  );
}
