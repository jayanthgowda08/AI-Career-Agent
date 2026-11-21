import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Compass,
  Briefcase,
  Sparkles,
  Bot,
  FileText,
  User,
  Bookmark,
  Target,
  BarChart3,
  Settings,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { logout, user } = useAuth();

  const navItems = [
    { to: '/dashboard/recommendations', label: 'Recommended Jobs', icon: Sparkles, badge: 'AI' },
    { to: '/dashboard/chat', label: 'Career Assistant', icon: Bot, badge: 'Agent' },
    { to: '/dashboard/jobs', label: 'Explore Jobs', icon: Briefcase },
    { to: '/dashboard/resume', label: 'Resume Analyzer', icon: FileText },
    { to: '/dashboard/skill-gap', label: 'Skill Gap Analysis', icon: Target },
    { to: '/dashboard/saved', label: 'Saved Jobs', icon: Bookmark },
    { to: '/dashboard/profile', label: 'Candidate Profile', icon: User },
    { to: '/dashboard/evaluations', label: 'System Analytics', icon: BarChart3 },
    { to: '/dashboard/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-bold text-base tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            AI Career Agent
          </span>
          <span className="block text-[10px] uppercase font-semibold text-indigo-400 tracking-wider">
            Agentic Platform
          </span>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Platform Menu
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* User Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-indigo-400">
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-200 truncate">{user?.email || 'Candidate'}</p>
              <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Connected
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            title="Log Out"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
