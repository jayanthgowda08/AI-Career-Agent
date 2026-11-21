import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, Sparkles, Target, Compass, ArrowRight, CheckCircle2, ShieldCheck, Database } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Navigation */}
      <header className="h-20 border-b border-slate-800/80 px-8 flex items-center justify-between max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            AI Career Agent
          </span>
        </div>

        <div className="flex items-center gap-4">
          <Link
            to="/auth"
            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-300 hover:text-white transition-colors"
          >
            Sign In
          </Link>
          <Link
            to="/auth?tab=register"
            className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/25 transition-all hover:scale-[1.02]"
          >
            Get Started Free
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-8 py-20 flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-8">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Autonomous LLM-Powered Career Platform</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-100 max-w-4xl leading-[1.15] mb-6">
          Find your dream tech role with{' '}
          <span className="bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-400 bg-clip-text text-transparent">
            Semantic Intelligence
          </span>
        </h1>

        <p className="text-lg md:text-xl text-slate-400 max-w-2xl font-normal leading-relaxed mb-10">
          Go beyond rigid keywords. Match your actual skills, experience, and aspirations using
          pgvector embeddings, multi-factor recommendation algorithms, and an autonomous AI agent.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 mb-20">
          <Link
            to="/auth?tab=register"
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-2 transition-all hover:scale-[1.02]"
          >
            <span>Launch Career Assistant</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/dashboard/jobs"
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-semibold bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-colors"
          >
            Browse Job Listings
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left w-full">
          <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/30 transition-all">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-6">
              <Bot className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">LangGraph Autonomous Agent</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Equipped with 8 concrete tools to search, compare, evaluate skill gaps, and save opportunities autonomously.
            </p>
          </div>

          <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/30 transition-all">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-6">
              <Database className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">pgvector Semantic Search</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Finds semantically similar positions even when your resume and job postings use differing terminology.
            </p>
          </div>

          <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/30 transition-all">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-6">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Actionable Skill Gap Analysis</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Identifies exact matching skills and missing competencies with actionable suggestions to become competitive.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-8 px-8 text-center text-xs text-slate-500">
        <p>© 2026 AI Career Agent Platform. Built with FastAPI, PostgreSQL + pgvector, LangGraph & React.</p>
      </footer>
    </div>
  );
}
