import React, { useState, useEffect, useCallback } from 'react';
import AdminLayout from './AdminLayout';
import { getSystemInfo } from '../../services/adminService';
import {
  Info,
  Server,
  Layers,
  Clock,
  Shield,
  FileCode,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { formatDate, formatTime } from '../../utils/formatters';

export default function AdminSystemInfoPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getSystemInfo();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to retrieve system telemetry.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const app = data?.application;
  const envInfo = data?.environment_info;
  const libs = data?.library_versions;
  const caps = data?.supported_capabilities;
  const sess = data?.session_configuration;
  const stamps = data?.activity_timestamps;

  return (
    <AdminLayout currentTab="info">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-white tracking-tight">
              System Telemetry & Architecture
            </h1>
            <p className="text-xs text-neutral-400 mt-0.5">
              Genuine runtime specifications, library versions, and server configuration.
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
            <span className="text-xs">Querying runtime environment and library telemetry...</span>
          </div>
        )}

        {data && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Box 1: Application & Runtime Status */}
            <div className="rounded-xl border border-[#262626] bg-[#161616] p-5 space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-[#222222] pb-3 text-sm font-semibold text-white">
                <Server className="w-4 h-4 text-emerald-400" />
                <span>Application & Service State</span>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Application Name:</span>
                  <span className="font-medium text-white">{app?.name || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Version:</span>
                  <span className="font-mono text-neutral-200">v{app?.version || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Environment:</span>
                  <span className="font-mono px-2 py-0.5 rounded bg-[#202020] text-emerald-400 border border-[#2b2b2b] uppercase text-[10px]">
                    {app?.environment || 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Backend API Status:</span>
                  <span className="flex items-center space-x-1.5 text-emerald-400 font-medium">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.7)]" />
                    <span className="capitalize">{app?.backend_status || 'Unknown'}</span>
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Frontend UI:</span>
                  <span className="flex items-center space-x-1.5 text-emerald-400 font-medium">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="capitalize">{app?.frontend_status || 'Connected'}</span>
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Host OS:</span>
                  <span className="font-mono text-neutral-300">
                    {envInfo?.os || 'Unknown'} ({envInfo?.os_release || 'Kernel'})
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Python Version:</span>
                  <span className="font-mono text-neutral-300">{envInfo?.python_version || 'Unknown'}</span>
                </div>
              </div>
            </div>

            {/* Box 2: Machine Learning & Python Libraries */}
            <div className="rounded-xl border border-[#262626] bg-[#161616] p-5 space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-[#222222] pb-3 text-sm font-semibold text-white">
                <FileCode className="w-4 h-4 text-purple-400" />
                <span>Machine Learning & Core Libraries</span>
              </div>

              <div className="space-y-2.5 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="font-sans text-neutral-400">FastAPI:</span>
                  <span className="text-neutral-200">{libs?.fastapi || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-sans text-neutral-400">XGBoost (xgboost):</span>
                  <span className="text-emerald-400 font-semibold">{libs?.xgboost || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-sans text-neutral-400">Scikit-Learn (sklearn):</span>
                  <span className="text-emerald-400 font-semibold">{libs?.scikit_learn || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-sans text-neutral-400">Pandas:</span>
                  <span className="text-neutral-200">{libs?.pandas || 'Unknown'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-sans text-neutral-400">NumPy:</span>
                  <span className="text-neutral-200">{libs?.numpy || 'Unknown'}</span>
                </div>
              </div>
            </div>

            {/* Box 3: Supported Capabilities & Formats */}
            <div className="rounded-xl border border-[#262626] bg-[#161616] p-5 space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-[#222222] pb-3 text-sm font-semibold text-white">
                <Layers className="w-4 h-4 text-blue-400" />
                <span>Supported Capabilities</span>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-neutral-400 block mb-1">Forecasting Algorithms:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {caps?.models?.map((m, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-[#202020] text-neutral-300 border border-[#2c2c2c] text-[11px]"
                      >
                        {m}
                      </span>
                    )) || 'Unknown'}
                  </div>
                </div>

                <div>
                  <span className="text-neutral-400 block mb-1">Spreadsheet File Formats:</span>
                  <div className="flex gap-2">
                    {caps?.file_formats?.map((fmt, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded bg-[#202020] text-emerald-400 font-mono text-[11px] border border-[#2c2c2c]"
                      >
                        {fmt}
                      </span>
                    )) || 'Unknown'}
                    <span className="text-neutral-500 self-center text-[11px]">
                      (Max {caps?.max_upload_size_mb || 25} MB)
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-neutral-400 block mb-1">Supported Time Frequencies:</span>
                  <div className="text-[11px] text-neutral-300">
                    {caps?.supported_frequencies?.join(', ') || 'Unknown'}
                  </div>
                </div>
              </div>
            </div>

            {/* Box 4: Session Lifecycle & Activity Timestamps */}
            <div className="rounded-xl border border-[#262626] bg-[#161616] p-5 space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-[#222222] pb-3 text-sm font-semibold text-white">
                <Clock className="w-4 h-4 text-amber-400" />
                <span>Session Lifecycle & Activity Timestamps</span>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Session TTL:</span>
                  <span className="font-mono text-neutral-200">
                    {sess?.session_expiry_minutes ? `${sess.session_expiry_minutes} mins` : 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Idle Timeout:</span>
                  <span className="font-mono text-neutral-200">
                    {sess?.session_idle_timeout_minutes ? `${sess.session_idle_timeout_minutes} mins` : 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-400">Disk Cleanup Interval:</span>
                  <span className="font-mono text-neutral-200">
                    {sess?.session_cleanup_interval_minutes ? `${sess.session_cleanup_interval_minutes} mins` : 'Unknown'}
                  </span>
                </div>

                <div className="pt-2 border-t border-[#222222] space-y-1.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-neutral-400">Last Training Run:</span>
                    <span className="text-neutral-300">
                      {stamps?.last_successful_training ? formatDate(stamps.last_successful_training) : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-neutral-400">Last Model Evaluation:</span>
                    <span className="text-neutral-300">
                      {stamps?.last_successful_evaluation ? formatDate(stamps.last_successful_evaluation) : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-neutral-400">Last Forecast Generated:</span>
                    <span className="text-neutral-300">
                      {stamps?.last_successful_forecast ? formatDate(stamps.last_successful_forecast) : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-neutral-400">Last Dataset Ingestion:</span>
                    <span className="text-neutral-300">
                      {stamps?.last_dataset_upload ? formatDate(stamps.last_dataset_upload) : '—'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
