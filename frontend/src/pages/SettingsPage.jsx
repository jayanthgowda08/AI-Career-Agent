import React from 'react';
import Navbar from '../components/Navbar';
import { Settings, Shield, Key, ExternalLink, Database, Server } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950">
      <Navbar
        title="Settings & System Configuration"
        subtitle="Manage application parameters, API links, and connected services"
      />

      <main className="p-8 max-w-4xl w-full mx-auto space-y-6">
        {/* Account Details */}
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-400" />
            <span>Account & Authentication</span>
          </h2>

          <div className="text-xs space-y-3">
            <div>
              <span className="text-slate-500 font-semibold block mb-0.5">Signed-in Email</span>
              <span className="text-slate-200 font-medium">{user?.email}</span>
            </div>
            <div>
              <span className="text-slate-500 font-semibold block mb-0.5">Authentication Mechanism</span>
              <span className="text-slate-200 font-medium">Bcrypt Password Hashing + JWT Stateless Token (HS256)</span>
            </div>
            <div>
              <span className="text-slate-500 font-semibold block mb-0.5">Candidate ID</span>
              <span className="font-mono text-slate-400 text-[11px]">{user?.id}</span>
            </div>
          </div>
        </div>

        {/* Backend & Model Diagnostics */}
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" />
            <span>Connected AI Architecture</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 font-semibold block mb-1">Primary LLM</span>
              <span className="text-white font-bold">Google Gemini 1.5 Flash</span>
              <p className="text-[11px] text-slate-500 mt-1">Configured for structured output & tool calling</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 font-semibold block mb-1">Embedding Model</span>
              <span className="text-white font-bold">all-MiniLM-L6-v2 (384-dim)</span>
              <p className="text-[11px] text-slate-500 mt-1">Local SentenceTransformers via pgvector</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 font-semibold block mb-1">Database Engine</span>
              <span className="text-white font-bold">PostgreSQL 16 + pgvector</span>
              <p className="text-[11px] text-slate-500 mt-1">Hybrid cosine distance search</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 font-semibold block mb-1">Agent Orchestrator</span>
              <span className="text-white font-bold">LangGraph StateGraph</span>
              <p className="text-[11px] text-slate-500 mt-1">Deterministic state machine with 8 tools</p>
            </div>
          </div>
        </div>

        {/* Developer Documentation Links */}
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-indigo-400" />
            <span>Developer & API Documentation</span>
          </h2>

          <div className="flex flex-wrap gap-3">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white flex items-center gap-2 border border-slate-700"
            >
              <span>Interactive Swagger UI (/docs)</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>

            <a
              href="http://localhost:8000/redoc"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white flex items-center gap-2 border border-slate-700"
            >
              <span>ReDoc Specification (/redoc)</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
