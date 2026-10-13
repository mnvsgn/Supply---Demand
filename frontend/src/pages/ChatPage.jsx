import React, { useState, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import { useTheme } from '../context/ThemeContext';
import Sidebar from '../components/layout/Sidebar';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import { PanelLeft, Sun, Moon } from 'lucide-react';

/**
 * ChatPage is the full-height workspace combining on/off Sidebar,
 * scrollable ChatWindow, and ChatInput (no top navbar).
 */
export default function ChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('demandiq_sidebar_open');
      if (saved !== null) return saved === 'true';
      return window.innerWidth >= 1024;
    }
    return true;
  });

  const { resetChat } = useChat();
  const { isDark, toggleTheme } = useTheme();

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => {
      const next = !prev;
      localStorage.setItem('demandiq_sidebar_open', String(next));
      return next;
    });
  };

  // Keyboard shortcuts:
  // - Ctrl+N / Cmd+N for New Forecast
  // - Ctrl+B / Cmd+B for Toggle Sidebar (standard shortcut)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        resetChat();
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        handleToggleSidebar();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [resetChat]);

  return (
    <div className="flex h-screen bg-[#121212] text-neutral-100 overflow-hidden selection:bg-emerald-600 selection:text-white">
      {/* On/Off Sidebar (collapsed 56px rail or expanded 260px drawer) */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={handleToggleSidebar}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Workspace (Full height, no navbar) */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative">
        {/* Floating Mobile Toggle Button when sidebar is closed */}
        {!sidebarOpen && (
          <button
            onClick={handleToggleSidebar}
            aria-label="Open sidebar"
            className="lg:hidden absolute top-3 left-3 z-30 p-2 rounded-lg bg-[#181818]/90 hover:bg-[#222222] text-neutral-400 hover:text-white border border-[#282828] shadow-md backdrop-blur-sm cursor-pointer transition-colors"
          >
            <PanelLeft className="w-4 h-4" />
          </button>
        )}

        {/* Floating Quick Theme Toggle Button (top-right corner) */}
        <button
          onClick={toggleTheme}
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          className="absolute top-3 right-4 z-30 flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-[#181818]/90 hover:bg-[#222222] text-neutral-300 hover:text-white border border-[#282828] shadow-sm backdrop-blur-sm cursor-pointer transition-colors text-xs"
        >
          {isDark ? (
            <>
              <Sun className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">Light</span>
            </>
          ) : (
            <>
              <Moon className="w-3.5 h-3.5 text-blue-400" />
              <span className="hidden sm:inline">Dark</span>
            </>
          )}
        </button>

        {/* Scrollable Conversation Stream */}
        <main className="flex-1 overflow-y-auto flex flex-col relative">
          <ChatWindow />
        </main>

        {/* Bottom Chat Input Bar */}
        <footer className="w-full bg-[#121212] pt-2">
          <ChatInput />
        </footer>
      </div>
    </div>
  );
}
