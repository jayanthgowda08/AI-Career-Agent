import React from 'react';
import { Sparkles, Bell, ExternalLink } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ title, subtitle }) {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-slate-900/60 backdrop-blur-md border-b border-slate-800/80 sticky top-0 z-20 flex items-center justify-between px-8">
      <div>
        <h1 className="text-lg font-bold text-slate-100 tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Model Badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/80 text-xs text-slate-300">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Gemini 1.5 Flash + pgvector</span>
        </div>

        {/* API Docs Link */}
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-700"
        >
          <span>FastAPI Docs</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </header>
  );
}
