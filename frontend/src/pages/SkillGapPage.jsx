import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import API from '../services/api';
import { Target, CheckCircle2, AlertTriangle, Lightbulb, Search } from 'lucide-react';

export default function SkillGapPage() {
  const [searchParams] = useSearchParams();
  const initialJobId = searchParams.get('jobId') || '';

  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(initialJobId);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load available jobs for the selector dropdown
  useEffect(() => {
    const loadJobs = async () => {
      try {
        const res = await API.get('/jobs?page_size=30');
        setJobs(res.data.jobs || []);
        if (!selectedJobId && res.data.jobs.length > 0) {
          setSelectedJobId(res.data.jobs[0].id);
        }
      } catch (err) {
        console.error("Failed to load jobs for selector:", err);
      }
    };
    loadJobs();
  }, []);

  // Fetch skill gap analysis whenever selectedJobId changes
  useEffect(() => {
    if (!selectedJobId) return;
    const fetchGap = async () => {
      setLoading(true);
      try {
        const res = await API.get(`/recommendations/skill-gap/${selectedJobId}`);
        setAnalysis(res.data);
      } catch (err) {
        console.error("Skill gap analysis failed:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchGap();
  }, [selectedJobId]);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950">
      <Navbar
        title="Skill Gap Diagnostics"
        subtitle="Compare your profile skills against target job specifications"
      />

      <main className="p-8 max-w-4xl w-full mx-auto space-y-6">
        {/* Job Selector Dropdown */}
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 space-y-3">
          <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider">
            Select Target Opportunity to Compare Against
          </label>
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-3 px-4 text-sm text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title} at {j.company} ({j.location})
              </option>
            ))}
          </select>
        </div>

        {/* Diagnostic Results Card */}
        {loading ? (
          <div className="h-96 rounded-3xl bg-slate-900/40 border border-slate-800 animate-pulse flex items-center justify-center text-slate-500 text-xs">
            Calculating skill overlaps and recommendations...
          </div>
        ) : analysis ? (
          <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-8">
            {/* Header / Score Banner */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b border-slate-800">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">Target Role</span>
                <h2 className="text-xl font-bold text-white mt-1">{analysis.job_title}</h2>
                <p className="text-xs text-slate-400">{analysis.company}</p>
              </div>

              <div className="flex items-center gap-4 bg-slate-950 p-4 rounded-2xl border border-slate-800">
                <div className="text-right">
                  <span className="text-xs font-semibold text-slate-400 block">Overall Skill Match</span>
                  <span className="text-2xl font-black text-indigo-400">{analysis.match_score}%</span>
                </div>
                <div className="w-12 h-12 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 flex items-center justify-center font-bold text-xs text-white">
                  {analysis.match_score}
                </div>
              </div>
            </div>

            {/* Skills Comparison Columns */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Matching Skills */}
              <div className="p-6 rounded-2xl bg-emerald-950/20 border border-emerald-500/25 space-y-3">
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                  <h3 className="text-sm font-bold">Skills You Already Have ({analysis.matching_skills.length})</h3>
                </div>
                {analysis.matching_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {analysis.matching_skills.map((s, idx) => (
                      <span key={idx} className="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 font-semibold text-xs border border-emerald-500/30">
                        {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">No overlapping skills found with this job post.</p>
                )}
              </div>

              {/* Missing Skills */}
              <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-500/25 space-y-3">
                <div className="flex items-center gap-2 text-rose-400">
                  <AlertTriangle className="w-5 h-5" />
                  <h3 className="text-sm font-bold">Skill Gaps to Address ({analysis.missing_required_skills.length})</h3>
                </div>
                {analysis.missing_required_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {analysis.missing_required_skills.map((s, idx) => (
                      <span key={idx} className="px-3 py-1 rounded-lg bg-rose-500/20 text-rose-300 font-semibold text-xs border border-rose-500/30">
                        {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-emerald-400 font-medium">You possess all required skills for this role!</p>
                )}
              </div>
            </div>

            {/* Actionable Recommendations */}
            <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400">
                <Lightbulb className="w-5 h-5" />
                <h3 className="text-sm font-bold text-white">Actionable Steps to Close the Gap</h3>
              </div>
              <ul className="space-y-2 text-xs text-slate-300">
                {analysis.recommendations_for_improvement.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0"></span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
