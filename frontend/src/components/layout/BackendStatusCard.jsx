import React from 'react';
import { Activity, CheckCircle2, AlertCircle, RefreshCw, Server } from 'lucide-react';

export default function BackendStatusCard({
  status,
  loading,
  error,
  lastChecked,
  onRefresh,
  apiUrl,
}) {
  const isHealthy = status?.status === 'healthy';

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-slate-800 text-blue-400">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Backend Health & API Gateway</h2>
            <p className="text-xs text-slate-400 font-mono">{apiUrl}</p>
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Checking...' : 'Check Health'}</span>
        </button>
      </div>

      {loading && !status && (
        <div className="py-6 flex items-center justify-center space-x-2 text-slate-400 text-sm">
          <Activity className="w-4 h-4 animate-spin text-blue-400" />
          <span>Querying FastAPI /api/v1/health...</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800/50 text-red-300 text-xs flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Connection Failed</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {isHealthy && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-slate-400 block text-[11px]">Status</span>
            <div className="flex items-center space-x-1.5 mt-0.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-medium text-emerald-400 capitalize">{status.status}</span>
            </div>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-slate-400 block text-[11px]">Service</span>
            <span className="font-medium text-slate-200 mt-0.5 block truncate">
              {status.service}
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-slate-400 block text-[11px]">Version</span>
            <span className="font-medium text-slate-200 mt-0.5 block font-mono">
              v{status.version}
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-slate-400 block text-[11px]">Environment</span>
            <span className="font-medium text-blue-300 mt-0.5 block uppercase text-[10px]">
              {status.environment}
            </span>
          </div>
        </div>
      )}

      {lastChecked && (
        <div className="mt-3 text-[11px] text-slate-500 text-right">
          Last verified: {lastChecked.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
