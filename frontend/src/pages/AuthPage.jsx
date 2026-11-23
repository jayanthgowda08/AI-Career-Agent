import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Bot, Mail, Lock, ArrowRight, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import API from '../services/api';

export default function AuthPage() {
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') === 'register' ? 'register' : 'login';
  const [isRegister, setIsRegister] = useState(initialTab === 'register');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [serverStatus, setServerStatus] = useState('checking'); // 'checking', 'online', 'waking'

  const { login, register } = useAuth();
  const navigate = useNavigate();

  // Check backend server status immediately on page load
  useEffect(() => {
    let isMounted = true;
    API.get('/health')
      .then(() => {
        if (isMounted) setServerStatus('online');
      })
      .catch(() => {
        if (isMounted) setServerStatus('waking');
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Timer while loading to show user live progress during cold starts
  useEffect(() => {
    let interval = null;
    if (loading) {
      setSecondsElapsed(0);
      interval = setInterval(() => {
        setSecondsElapsed((prev) => prev + 1);
      }, 1000);
    } else {
      setSecondsElapsed(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        await register(email, password);
      } else {
        await login(email, password);
      }
      navigate('/dashboard/recommendations');
    } catch (err) {
      console.error("Auth error details:", err);
      if (!err.response) {
        setError('Cannot connect to backend server. On free hosting (Render), the backend spins down when idle and can take 25–35 seconds to wake up on the first request. Please wait a moment and try again.');
      } else {
        const detail = err.response.data?.detail;
        if (typeof detail === 'string') {
          setError(detail);
        } else if (Array.isArray(detail) && detail.length > 0) {
          setError(detail[0]?.msg || 'Validation error.');
        } else {
          setError('Authentication failed. Please check your credentials.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-6 selection:bg-indigo-500 selection:text-white">
      {/* Brand Header */}
      <Link to="/" className="flex items-center gap-3 mb-6 group">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <span className="font-extrabold text-2xl tracking-tight text-white">AI Career Agent</span>
      </Link>

      {/* Cloud Server Live Status Pill */}
      <div className="mb-4 flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px]">
        <span
          className={`w-2 h-2 rounded-full ${
            serverStatus === 'online'
              ? 'bg-emerald-400 animate-pulse'
              : serverStatus === 'waking'
              ? 'bg-amber-400 animate-ping'
              : 'bg-slate-500'
          }`}
        />
        <span className="text-slate-400">
          Backend Cloud:
          {serverStatus === 'online' && <strong className="text-emerald-400 ml-1">Online (Ready)</strong>}
          {serverStatus === 'waking' && <strong className="text-amber-400 ml-1">Waking up (~25s)...</strong>}
          {serverStatus === 'checking' && <span className="text-slate-400 ml-1">Connecting...</span>}
        </span>
      </div>

      {/* Card */}
      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-3xl p-8 shadow-2xl backdrop-blur-xl">
        {/* Toggle Tabs */}
        <div className="flex bg-slate-950 p-1 rounded-xl mb-6 border border-slate-800">
          <button
            type="button"
            onClick={() => { setIsRegister(false); setError(null); }}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
              !isRegister ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setError(null); }}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
              isRegister ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@example.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="•••••••• (min 8 characters)"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-sm shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 mt-2"
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Signing in... ({secondsElapsed}s)</span>
              </div>
            ) : (
              <>
                <span>{isRegister ? 'Register & Continue' : 'Sign In to Dashboard'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          {loading && (
            <div className="pt-2 text-center space-y-1">
              <p className="text-xs text-amber-300 font-medium">
                ⚡ Authenticating... {secondsElapsed}s elapsed
              </p>
              {secondsElapsed > 2 && (
                <p className="text-[11px] text-slate-400 animate-pulse">
                  Cloud container waking from idle (~25s on first request). Please keep this tab open...
                </p>
              )}
            </div>
          )}
        </form>

        <p className="mt-6 text-center text-xs text-slate-500">
          Secured with Bcrypt password hashing & JWT tokens.
        </p>
      </div>
    </div>
  );
}
