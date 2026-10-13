import React, { useEffect } from 'react';
import { useRouter, Link } from '../../context/RouterContext';
import { useTheme } from '../../context/ThemeContext';
import {
  isAuthenticated,
  getAdminUsername,
  logout,
} from '../../services/adminService';
import {
  BarChart3,
  LayoutDashboard,
  LineChart,
  Info,
  LogOut,
  MessageSquare,
  ShieldAlert,
  Sun,
  Moon,
} from 'lucide-react';

export default function AdminLayout({ children, currentTab = 'dashboard' }) {
  const { currentPath, navigate } = useRouter();
  const { isDark, toggleTheme } = useTheme();
  const username = getAdminUsername();

  // Authentication Guard: redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/admin/login');
    }
  }, [navigate]);

  const handleLogout = async () => {
    await logout();
    navigate('/admin/login');
  };

  const navItems = [
    {
      to: '/admin',
      label: 'Dashboard',
      icon: LayoutDashboard,
      active: currentPath === '/admin',
    },
    {
      to: '/admin/performance',
      label: 'Model Performance',
      icon: LineChart,
      active: currentPath === '/admin/performance',
    },
    {
      to: '/admin/info',
      label: 'System Information',
      icon: Info,
      active: currentPath === '/admin/info',
    },
  ];

  return (
    <div className="min-h-screen bg-[#121212] text-neutral-100 flex flex-col selection:bg-emerald-600 selection:text-white">
      {/* Admin Top Header */}
      <header className="h-14 border-b border-[#212121] bg-[#141414] sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6">
        {/* Brand & Admin Badge */}
        <div className="flex items-center space-x-3">
          <Link to="/admin" className="flex items-center space-x-2.5 group">
            <div className="w-7 h-7 rounded-lg bg-[#193228] text-emerald-400 border border-[#234b3c] flex items-center justify-center flex-shrink-0">
              <BarChart3 className="w-4 h-4" />
            </div>
            <span className="font-semibold text-sm text-white tracking-tight">
              DemandIQ
            </span>
          </Link>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#202020] text-emerald-400 border border-[#2c2c2c]">
            Admin
          </span>
        </div>

        {/* Right side: Theme Toggle, Chat link & Admin User Actions */}
        <div className="flex items-center space-x-2.5 sm:space-x-3">
          <button
            onClick={toggleTheme}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            className="flex items-center space-x-1.5 text-xs text-neutral-300 hover:text-white px-2.5 py-1.5 rounded-lg bg-[#1c1c1c] hover:bg-[#242424] border border-[#2a2a2a] transition-colors cursor-pointer"
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

          <Link
            to="/"
            className="flex items-center space-x-1.5 text-xs text-neutral-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-[#1f1f1f] transition-colors"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chat Workspace</span>
          </Link>

          <div className="h-4 w-px bg-[#262626]" />

          <span className="text-xs text-neutral-400 hidden sm:inline">
            Logged in as <strong className="text-neutral-200">{username}</strong>
          </span>

          <button
            onClick={handleLogout}
            title="Log out administrator"
            className="flex items-center space-x-1.5 text-xs text-rose-400 hover:text-rose-300 px-2.5 py-1.5 rounded-lg hover:bg-rose-950/30 border border-transparent hover:border-rose-900/40 transition-colors cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Subnav Tab Bar */}
      <div className="border-b border-[#212121] bg-[#161616] px-4 sm:px-6">
        <nav className="flex space-x-1 sm:space-x-4 max-w-7xl mx-auto overflow-x-auto py-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center space-x-2 px-3 py-2 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
                  item.active
                    ? 'bg-[#222222] text-white border border-[#303030]'
                    : 'text-neutral-400 hover:text-neutral-200 hover:bg-[#1a1a1a]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${item.active ? 'text-emerald-400' : ''}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {children}
      </main>

      {/* Admin Footer */}
      <footer className="border-t border-[#212121] bg-[#141414] py-3 px-6 text-center text-xs text-neutral-500">
        DemandIQ Administrative Telemetry • Local JSON-based metrics store (No database)
      </footer>
    </div>
  );
}
