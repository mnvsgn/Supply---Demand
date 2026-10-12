import React from 'react';
import { useChat } from '../../context/ChatContext';
import { Link } from '../../context/RouterContext';
import {
  PanelLeft,
  Plus,
  Database,
  Sparkles,
  Cpu,
  BarChart3,
  FileSpreadsheet,
  RefreshCw,
  Layers,
  Calendar,
  LayoutDashboard,
} from 'lucide-react';
import { formatInteger } from '../../utils/formatters';

export default function Sidebar({ isOpen, onToggle, onClose }) {
  const {
    sessionId,
    activeDataset,
    backendConnected,
    checkBackendHealth,
    resetChat,
    handleSendPrompt,
    isForecasting,
    isEvaluating,
    isAnalyzing,
  } = useChat();

  const handleNewForecast = () => {
    resetChat();
    if (onClose && window.innerWidth < 1024) {
      onClose();
    }
  };

  const handlePromptClick = (promptText) => {
    handleSendPrompt(promptText);
    if (onClose && window.innerWidth < 1024) {
      onClose();
    }
  };

  const quickPrompts = [
    {
      title: 'Forecast next 14 days',
      desc: 'Auto-select best ML algorithm & intervals',
      prompt: 'Forecast total demand for the next 14 days',
    },
    {
      title: 'Sales Trends & Safety Stock',
      desc: 'Run rate, seasonality & inventory ROP',
      prompt: 'Show sales trends, seasonality and safety stock for 7 days lead time',
    },
    {
      title: 'Forecast next 30 days',
      desc: 'Extended monthly horizon with XGBoost',
      prompt: 'Forecast demand for the next 30 days using XGBoost',
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* ============================================================== */}
      {/* COLLAPSED RAIL VIEW (when sidebar state is OFF on desktop)      */}
      {/* ============================================================== */}
      {!isOpen && (
        <aside
          className="hidden lg:flex w-14 h-full bg-[#141414] border-r border-[#262626] flex-col justify-between items-center py-2.5 z-30 flex-shrink-0 select-none overflow-visible"
          aria-label="Collapsed sidebar navigation"
        >
          {/* Top Action Icons */}
          <div className="flex flex-col items-center space-y-1.5 w-full px-2">
            {/* 1. Toggle Sidebar Button */}
            <div className="relative group w-full flex justify-center">
              <button
                onClick={onToggle}
                aria-label="Expand sidebar"
                title="Expand sidebar"
                className="w-10 h-10 rounded-lg flex items-center justify-center text-neutral-400 hover:text-white hover:bg-[#212121] transition-colors cursor-pointer"
              >
                <PanelLeft className="w-5 h-5 stroke-[1.75]" />
              </button>
              <div className="absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 px-2.5 py-1 bg-[#212121] text-neutral-100 text-xs font-normal rounded-md shadow-xl border border-[#303030] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                Expand sidebar (Ctrl+B)
              </div>
            </div>

            {/* 2. New Forecast Button */}
            <div className="relative group w-full flex justify-center">
              <button
                onClick={handleNewForecast}
                aria-label="New forecast"
                className="w-10 h-10 rounded-lg flex items-center justify-center text-neutral-400 hover:text-white hover:bg-[#212121] transition-colors cursor-pointer"
              >
                <Plus className="w-5 h-5 text-emerald-400 stroke-[2]" />
              </button>
              <div className="absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 px-2.5 py-1 bg-[#212121] text-neutral-100 text-xs font-normal rounded-md shadow-xl border border-[#303030] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                New Forecast (Ctrl+N)
              </div>
            </div>

            {/* 3. Active Dataset Status */}
            <div className="relative group w-full flex justify-center">
              <button
                onClick={onToggle}
                aria-label="Dataset"
                className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${
                  activeDataset
                    ? 'text-emerald-400 bg-[#193228]/50 hover:bg-[#193228]'
                    : 'text-neutral-400 hover:text-white hover:bg-[#212121]'
                }`}
              >
                <Database className="w-5 h-5 stroke-[1.75]" />
              </button>
              <div className="absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 px-2.5 py-1 bg-[#212121] text-neutral-100 text-xs font-normal rounded-md shadow-xl border border-[#303030] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                {activeDataset ? `Active: ${activeDataset.filename}` : 'No dataset loaded'}
              </div>
            </div>

            {/* 4. Quick Prompts */}
            <div className="relative group w-full flex justify-center">
              <button
                onClick={onToggle}
                aria-label="Quick Prompts"
                className="w-10 h-10 rounded-lg flex items-center justify-center text-neutral-400 hover:text-white hover:bg-[#212121] transition-colors cursor-pointer"
              >
                <Sparkles className="w-5 h-5 stroke-[1.75]" />
              </button>
              <div className="absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 px-2.5 py-1 bg-[#212121] text-neutral-100 text-xs font-normal rounded-md shadow-xl border border-[#303030] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                Forecasting Prompts
              </div>
            </div>

            {/* 5. ML Models */}
            <div className="relative group w-full flex justify-center">
              <button
                onClick={onToggle}
                aria-label="ML Architecture"
                className="w-10 h-10 rounded-lg flex items-center justify-center text-neutral-400 hover:text-white hover:bg-[#212121] transition-colors cursor-pointer"
              >
                <Cpu className="w-5 h-5 stroke-[1.75]" />
              </button>
              <div className="absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 px-2.5 py-1 bg-[#212121] text-neutral-100 text-xs font-normal rounded-md shadow-xl border border-[#303030] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                ML Architecture (Naive, RF, XGBoost)
              </div>
            </div>

            {/* 6. Admin Dashboard */}
            <div className="relative group w-full flex justify-center">
              <Link
                to="/admin"
                aria-label="Admin Dashboard"
                className="w-10 h-10 rounded-lg flex items-center justify-center text-neutral-400 hover:text-white hover:bg-[#212121] transition-colors cursor-pointer"
              >
                <LayoutDashboard className="w-5 h-5 stroke-[1.75]" />
              </Link>
              <div className="absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 px-2.5 py-1 bg-[#212121] text-neutral-100 text-xs font-normal rounded-md shadow-xl border border-[#303030] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                Admin Dashboard (/admin)
              </div>
            </div>
          </div>

          {/* Bottom Backend Indicator */}
          <div className="relative group pb-1">
            <button
              onClick={checkBackendHealth}
              aria-label="Backend Status"
              className="w-8 h-8 rounded-full flex items-center justify-center bg-[#1c1c1c] hover:bg-[#262626] border border-[#2a2a2a] transition-colors cursor-pointer"
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  backendConnected === true
                    ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.7)]'
                    : backendConnected === false
                    ? 'bg-rose-500'
                    : 'bg-amber-400 animate-pulse'
                }`}
              />
            </button>
            <div className="absolute left-[calc(100%+8px)] bottom-1 px-2.5 py-1 bg-[#212121] text-neutral-100 text-xs font-normal rounded-md shadow-xl border border-[#303030] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
              {backendConnected === true
                ? 'FastAPI Connected'
                : backendConnected === false
                ? 'Backend Offline'
                : 'Checking Backend...'}
            </div>
          </div>
        </aside>
      )}

      {/* ============================================================== */}
      {/* EXPANDED SIDEBAR VIEW (when sidebar state is ON)                */}
      {/* ============================================================== */}
      {isOpen && (
        <aside
          className="fixed lg:static top-0 bottom-0 left-0 z-50 w-[260px] h-full bg-[#141414] border-r border-[#262626] flex flex-col justify-between flex-shrink-0 select-none transition-all duration-200"
          aria-label="Expanded sidebar navigation"
        >
          {/* Top Container */}
          <div className="flex flex-col flex-1 min-h-0">
            {/* Header: Brand + Toggle Close Button */}
            <div className="h-13 px-3.5 flex items-center justify-between border-b border-[#212121]">
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-7 h-7 rounded-lg bg-[#193228] text-emerald-400 border border-[#234b3c] flex items-center justify-center flex-shrink-0">
                  <BarChart3 className="w-4 h-4" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-sm font-semibold text-white tracking-tight leading-tight truncate">
                    DemandIQ
                  </span>
                  <span className="text-[10px] text-neutral-500 tracking-tight leading-tight">
                    Supply & Demand
                  </span>
                </div>
              </div>

              {/* Collapse Sidebar Button */}
              <button
                onClick={onToggle}
                title="Collapse sidebar (Ctrl+B)"
                aria-label="Collapse sidebar"
                className="w-7 h-7 rounded-md hover:bg-[#212121] text-neutral-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
              >
                <PanelLeft className="w-4 h-4 stroke-[1.75]" />
              </button>
            </div>

            {/* Primary Action Button: New Forecast */}
            <div className="p-3 border-b border-[#212121]">
              <button
                onClick={handleNewForecast}
                className="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-[#1c1c1c] hover:bg-[#242424] text-neutral-200 hover:text-white border border-[#2a2a2a] transition-colors cursor-pointer"
                aria-label="Start new forecast chat"
              >
                <div className="flex items-center space-x-2">
                  <Plus className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-medium">New Forecast</span>
                </div>
                <span className="text-[10px] text-neutral-500 font-mono">Ctrl+N</span>
              </button>
            </div>

            {/* Scrollable Middle Content */}
            <div className="flex-1 overflow-y-auto px-2.5 py-3 space-y-4 scrollbar-thin scrollbar-thumb-[#262626]">
              {/* Active Dataset Section */}
              <div>
                <div className="text-[11px] font-medium text-neutral-400 px-1 pb-1.5 flex items-center justify-between">
                  <span>Active Dataset</span>
                  {activeDataset && (
                    <span className="text-[10px] text-emerald-400 font-mono">
                      {activeDataset.is_mapped ? 'Mapped' : 'Uploaded'}
                    </span>
                  )}
                </div>

                {activeDataset ? (
                  <div className="rounded-xl border border-[#262626] bg-[#181818] p-2.5 space-y-2">
                    <div className="flex items-center space-x-2 min-w-0">
                      <FileSpreadsheet className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <span className="text-xs font-medium text-neutral-200 truncate" title={activeDataset.filename}>
                        {activeDataset.filename}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-1 text-[11px] text-neutral-400 pt-1 border-t border-[#262626]">
                      <div>
                        <span className="text-neutral-500 text-[10px] block">Rows:</span>
                        <span className="text-neutral-300 font-medium">{formatInteger(activeDataset.row_count)}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500 text-[10px] block">Columns:</span>
                        <span className="text-neutral-300 font-medium">{activeDataset.column_count}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-[#262626] bg-[#171717] p-2.5 text-center">
                    <p className="text-xs text-neutral-400">No dataset loaded</p>
                    <p className="text-[11px] text-neutral-500 mt-0.5">Upload CSV or XLSX in chat.</p>
                  </div>
                )}
              </div>

              {/* Forecasting Prompts Section */}
              <div>
                <div className="text-[11px] font-medium text-neutral-400 px-1 pb-1.5 flex items-center justify-between">
                  <span>Forecasting Prompts</span>
                  <Sparkles className="w-3 h-3 text-neutral-500" />
                </div>

                <div className="space-y-1">
                  {quickPrompts.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => handlePromptClick(item.prompt)}
                      disabled={isForecasting || isEvaluating || isAnalyzing}
                      className="w-full text-left p-2 rounded-lg hover:bg-[#202020] text-neutral-300 hover:text-white border border-transparent hover:border-[#2a2a2a] transition-colors text-xs group disabled:opacity-50 cursor-pointer"
                    >
                      <div className="font-medium text-neutral-200 group-hover:text-emerald-300 transition-colors truncate">
                        {item.title}
                      </div>
                      <div className="text-[11px] text-neutral-500 mt-0.5 truncate">{item.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Footer: Session & Backend Connectivity */}
          <div className="p-2.5 border-t border-[#212121] bg-[#141414] space-y-2">
            {/* Admin Portal Shortcut */}
            <Link
              to="/admin"
              className="flex items-center justify-between p-2 rounded-lg bg-[#181818] hover:bg-[#202020] text-xs text-neutral-300 hover:text-white border border-[#262626] transition-colors"
            >
              <div className="flex items-center space-x-2">
                <LayoutDashboard className="w-3.5 h-3.5 text-emerald-400" />
                <span>Admin Dashboard</span>
              </div>
              <span className="text-[10px] text-neutral-500 font-mono">/admin</span>
            </Link>

            <div className="flex items-center justify-between rounded-lg bg-[#181818] border border-[#262626] p-2 text-xs">
              <div className="flex items-center space-x-2 min-w-0">
                <span
                  className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    backendConnected === true
                      ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.7)]'
                      : backendConnected === false
                      ? 'bg-rose-500'
                      : 'bg-amber-400 animate-pulse'
                  }`}
                />
                <div className="flex flex-col min-w-0">
                  <span className="text-neutral-300 font-medium text-[11px] truncate">
                    {backendConnected === true
                      ? 'FastAPI Connected'
                      : backendConnected === false
                      ? 'Backend Offline'
                      : 'Connecting...'}
                  </span>
                  <span className="text-[10px] text-neutral-500 font-mono truncate" title={sessionId || 'Active'}>
                    {sessionId ? `${sessionId.substring(0, 10)}...` : 'Active session'}
                  </span>
                </div>
              </div>
              <button
                onClick={checkBackendHealth}
                title="Refresh backend status"
                aria-label="Refresh status"
                className="p-1 rounded text-neutral-400 hover:text-white hover:bg-[#222222] transition-colors cursor-pointer flex-shrink-0"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </aside>
      )}
    </>
  );
}
