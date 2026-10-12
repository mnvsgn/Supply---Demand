import React from 'react';
import { useChat } from '../../context/ChatContext';
import {
  BarChart3,
  PanelLeft,
  RefreshCw,
} from 'lucide-react';

export default function Navbar({ onToggleSidebar }) {
  const { backendConnected, checkBackendHealth } = useChat();

  return (
    <header className="h-13 border-b border-[#212121] bg-[#141414] sticky top-0 z-20 flex items-center justify-between px-3.5 sm:px-5">
      {/* Left side: Mobile Toggle & Brand */}
      <div className="flex items-center space-x-2.5">
        {/* Mobile Toggle Button */}
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
          title="Toggle sidebar"
          className="lg:hidden p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-[#202020] transition-colors"
        >
          <PanelLeft className="w-5 h-5" />
        </button>

        {/* Brand Name */}
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-md bg-[#193228] text-emerald-400 border border-[#234b3c] flex items-center justify-center flex-shrink-0">
            <BarChart3 className="w-3.5 h-3.5" />
          </div>
          <span className="font-semibold text-sm text-neutral-100 tracking-tight">
            DemandIQ
          </span>
          <span className="hidden sm:inline-block text-[11px] text-neutral-500 pl-1 border-l border-[#262626]">
            Forecasting Workspace
          </span>
        </div>
      </div>

      {/* Right side: Backend Health Indicator */}
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#181818] border border-[#262626] text-[11px]">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              backendConnected === true
                ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]'
                : backendConnected === false
                ? 'bg-rose-500'
                : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span className="text-neutral-300 font-medium hidden sm:inline">
            {backendConnected === true
              ? 'FastAPI Connected'
              : backendConnected === false
              ? 'Backend Offline'
              : 'Connecting...'}
          </span>
          <button
            onClick={checkBackendHealth}
            title="Refresh status"
            aria-label="Refresh status"
            className="text-neutral-500 hover:text-neutral-300 transition-colors ml-1 cursor-pointer"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>
      </div>
    </header>
  );
}
