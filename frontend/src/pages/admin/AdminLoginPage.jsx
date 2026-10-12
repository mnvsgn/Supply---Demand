import React, { useState } from 'react';
import { useRouter, Link } from '../../context/RouterContext';
import { login, isAuthenticated } from '../../services/adminService';
import { BarChart3, Lock, User, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';

export default function AdminLoginPage() {
  const { navigate } = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // If already authenticated, redirect to /admin
  React.useEffect(() => {
    if (isAuthenticated()) {
      navigate('/admin');
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please enter both administrator username and password.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await login(username.trim(), password);
      navigate('/admin');
    } catch (err) {
      setError(err.message || 'Invalid administrator username or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#121212] text-neutral-100 flex flex-col items-center justify-center p-4 selection:bg-emerald-600 selection:text-white">
      {/* Back to chat link */}
      <div className="w-full max-w-sm mb-4">
        <Link
          to="/"
          className="inline-flex items-center space-x-1.5 text-xs text-neutral-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Chat Workspace</span>
        </Link>
      </div>

      {/* Login Card */}
      <div className="w-full max-w-sm rounded-2xl border border-[#262626] bg-[#161616] p-6 sm:p-8 shadow-xl space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-10 h-10 rounded-xl bg-[#193228] text-emerald-400 border border-[#234b3c] flex items-center justify-center mx-auto shadow-sm">
            <BarChart3 className="w-5 h-5" />
          </div>
          <h1 className="text-lg font-semibold text-white tracking-tight">
            DemandIQ Administration
          </h1>
          <p className="text-xs text-neutral-400">
            Sign in to access system telemetry, model performance & operational audits.
          </p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="flex items-start space-x-2 text-xs text-rose-300 bg-rose-950/40 border border-rose-900/50 rounded-lg p-3">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">{error}</div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-neutral-300">
              Admin Username
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-neutral-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                disabled={loading}
                required
                className="w-full bg-[#1b1b1b] border border-[#2e2e2e] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-neutral-300">
              Admin Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-neutral-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                disabled={loading}
                required
                className="w-full bg-[#1b1b1b] border border-[#2e2e2e] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-medium transition-colors shadow-sm cursor-pointer flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <span>Sign In to Admin</span>
            )}
          </button>
        </form>

        <div className="pt-2 text-center text-[11px] text-neutral-500 border-t border-[#222222]">
          Credentials are strictly validated against server environment variables.
        </div>
      </div>
    </div>
  );
}
