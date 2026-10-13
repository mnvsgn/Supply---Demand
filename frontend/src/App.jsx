import React from 'react';
import { RouterProvider, useRouter } from './context/RouterContext';
import { ChatProvider } from './context/ChatContext';
import { ThemeProvider } from './context/ThemeContext';
import ChatPage from './pages/ChatPage';
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import AdminPerformancePage from './pages/admin/AdminPerformancePage';
import AdminSystemInfoPage from './pages/admin/AdminSystemInfoPage';
import AdminLoginPage from './pages/admin/AdminLoginPage';
import ErrorBoundary from './components/common/ErrorBoundary';

function RouteSwitch() {
  const { currentPath } = useRouter();

  // Normalize path by stripping trailing slashes
  const path = currentPath.length > 1 ? currentPath.replace(/\/+$/, '') : currentPath;

  if (path === '/admin') {
    return <AdminDashboardPage />;
  }
  if (path === '/admin/performance') {
    return <AdminPerformancePage />;
  }
  if (path === '/admin/info') {
    return <AdminSystemInfoPage />;
  }
  if (path === '/admin/login') {
    return <AdminLoginPage />;
  }

  // Default: Main Supply & Demand Chat Workspace
  return (
    <ChatProvider>
      <ChatPage />
    </ChatProvider>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <RouterProvider>
          <RouteSwitch />
        </RouterProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
