import React, { useState, useEffect, useCallback } from 'react';
import AdminLayout from './AdminLayout';
import { getDashboard } from '../../services/adminService';
import {
  Cpu,
  Database,
  LineChart,
  Layers,
  RefreshCw,
  Loader2,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  TrendingUp,
} from 'lucide-react';
import { formatInteger, formatDate, formatTime, formatPercentage } from '../../utils/formatters';

export default function AdminDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDashboard();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getActivityBadge = (type) => {
    switch (type) {
      case 'training':
        return 'bg-purple-950/40 text-purple-400 border-purple-800/40';
      case 'evaluation':
        return 'bg-blue-950/40 text-blue-400 border-blue-800/40';
      case 'upload':
        return 'bg-emerald-950/40 text-emerald-400 border-emerald-800/40';
      case 'forecast':
        return 'bg-amber-950/40 text-amber-400 border-amber-800/40';
      case 'verification':
        return 'bg-cyan-950/40 text-cyan-400 border-cyan-800/40';
      default:
        return 'bg-neutral-800 text-neutral-400 border-neutral-700';
    }
  };

  return (
    <AdminLayout currentTab="dashboard">
      <div className="space-y-6">
        {/* Page Title & Refresh Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-white tracking-tight">
              Administrative Dashboard
            </h1>
            <p className="text-xs text-neutral-400 mt-0.5">
              Live telemetry and historical activity logs stored in local JSON storage.
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

        {/* Error Notification */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-900/50 flex items-center space-x-2.5 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading Spinner */}
        {loading && !data && (
          <div className="py-20 flex flex-col items-center justify-center space-y-3 text-neutral-400">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
            <span className="text-xs">Reading metrics from JSON repository...</span>
          </div>
        )}

        {data && (
          <>
            {/* Top 4 Primary Counters */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Card 1: Training Runs */}
              <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-2">
                <div className="flex items-center justify-between text-neutral-400 text-xs">
                  <span>Training Runs</span>
                  <Cpu className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {formatInteger(data.total_training_runs)}
                </div>
                <div className="text-[11px] text-neutral-500 truncate">
                  Last: {data.timestamps?.last_training_time ? formatDate(data.timestamps.last_training_time) : 'No runs yet'}
                </div>
              </div>

              {/* Card 2: Evaluated Models */}
              <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-2">
                <div className="flex items-center justify-between text-neutral-400 text-xs">
                  <span>Evaluated Models</span>
                  <LineChart className="w-4 h-4 text-blue-400" />
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {formatInteger(data.total_evaluated_models)}
                </div>
                <div className="text-[11px] text-neutral-500 truncate">
                  Last: {data.timestamps?.last_evaluation_time ? formatDate(data.timestamps.last_evaluation_time) : 'No backtests yet'}
                </div>
              </div>

              {/* Card 3: Forecasts Generated */}
              <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-2">
                <div className="flex items-center justify-between text-neutral-400 text-xs">
                  <span>Forecasts Generated</span>
                  <TrendingUp className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {formatInteger(data.total_forecasts_generated)}
                </div>
                <div className="text-[11px] text-neutral-500 truncate">
                  Last: {data.timestamps?.last_forecast_time ? formatDate(data.timestamps.last_forecast_time) : 'No forecasts yet'}
                </div>
              </div>

              {/* Card 4: Datasets Processed */}
              <div className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-2">
                <div className="flex items-center justify-between text-neutral-400 text-xs">
                  <span>User Datasets</span>
                  <Database className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {formatInteger(data.user_datasets_processed)}
                </div>
                <div className="text-[11px] text-neutral-500 truncate">
                  Last: {data.timestamps?.last_upload_time ? formatDate(data.timestamps.last_upload_time) : 'No uploads yet'}
                </div>
              </div>
            </div>

            {/* Algorithm Status Grid */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-white tracking-tight">
                Forecasting Algorithm Status
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {data.model_statuses?.map((m) => {
                  const isEvaluated = m.status === 'evaluated' || m.status === 'trained';
                  return (
                    <div
                      key={m.key}
                      className="rounded-xl border border-[#262626] bg-[#161616] p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-sm text-neutral-200">
                          {m.name}
                        </span>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                            isEvaluated
                              ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/40'
                              : 'bg-neutral-800/60 text-neutral-400 border-neutral-700'
                          }`}
                        >
                          {m.status === 'not_evaluated' ? 'Not evaluated' : m.status}
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[#222222] text-xs">
                        <div>
                          <span className="text-[10px] text-neutral-500 block">WAPE</span>
                          <span className="font-mono text-neutral-200">
                            {m.best_wape !== null ? formatPercentage(m.best_wape) : '—'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-neutral-500 block">MAE</span>
                          <span className="font-mono text-neutral-200">
                            {m.best_mae !== null ? m.best_mae.toFixed(2) : '—'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-neutral-500 block">RMSE</span>
                          <span className="font-mono text-neutral-200">
                            {m.best_rmse !== null ? m.best_rmse.toFixed(2) : '—'}
                          </span>
                        </div>
                      </div>

                      <div className="text-[11px] text-neutral-500 pt-1">
                        {m.last_evaluated
                          ? `Last evaluated: ${formatDate(m.last_evaluated)} ${formatTime(m.last_evaluated)}`
                          : 'No training or evaluation has occurred yet.'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Recent Activity Audit Log */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-white tracking-tight">
                Recent System Activity
              </h2>

              {(!data.recent_activity || data.recent_activity.length === 0) ? (
                <div className="rounded-xl border border-dashed border-[#262626] bg-[#161616] p-8 text-center text-xs text-neutral-500">
                  No activity recorded yet. Ingest a dataset or execute a forecast in the chat workspace to record activity.
                </div>
              ) : (
                <div className="rounded-xl border border-[#262626] bg-[#161616] overflow-hidden divide-y divide-[#222222]">
                  {data.recent_activity.map((act) => (
                    <div
                      key={act.activity_id}
                      className="p-3.5 flex items-start justify-between gap-3 text-xs hover:bg-[#1a1a1a] transition-colors"
                    >
                      <div className="flex items-start space-x-3 min-w-0">
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded border capitalize flex-shrink-0 mt-0.5 ${getActivityBadge(
                            act.type
                          )}`}
                        >
                          {act.type}
                        </span>
                        <div className="min-w-0 space-y-0.5">
                          <div className="font-medium text-neutral-200">
                            {act.title}
                          </div>
                          <div className="text-[11px] text-neutral-400 truncate">
                            {act.description}
                          </div>
                        </div>
                      </div>

                      <span className="text-[11px] text-neutral-500 flex-shrink-0 font-mono">
                        {formatDate(act.timestamp)} {formatTime(act.timestamp)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AdminLayout>
  );
}
