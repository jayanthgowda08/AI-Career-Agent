import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import API from '../services/api';
import {
  Building,
  MapPin,
  DollarSign,
  Calendar,
  Briefcase,
  Bookmark,
  ExternalLink,
  Target,
  ArrowLeft,
  CheckCircle2,
} from 'lucide-react';

export default function JobDetailsPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const res = await API.get(`/jobs/${jobId}`);
        setJob(res.data);
      } catch (err) {
        console.error("Failed to load job:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchJob();
  }, [jobId]);

  const toggleBookmark = async () => {
    try {
      if (saved) {
        await API.delete(`/agent/saved-jobs/${jobId}`);
        setSaved(false);
      } else {
        await API.post(`/agent/saved-jobs/${jobId}`);
        setSaved(true);
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-slate-950 p-8 text-center">
        <h2 className="text-xl font-bold text-white mb-2">Job Not Found</h2>
        <p className="text-xs text-slate-400 mb-6">This job listing may have expired or been removed.</p>
        <Link to="/dashboard/jobs" className="px-4 py-2 bg-indigo-600 rounded-xl text-xs font-semibold text-white">
          Back to Jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950">
      <Navbar title={job.title} subtitle={`${job.company} • ${job.location}`} />

      <main className="p-8 max-w-4xl w-full mx-auto space-y-6">
        <Link
          to="/dashboard/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Explore</span>
        </Link>

        {/* Hero Card */}
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">{job.title}</h1>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1 font-semibold text-slate-200">
                  <Building className="w-4 h-4 text-slate-500" />
                  {job.company}
                </span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4 text-slate-500" />
                  {job.location}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4 text-slate-500" />
                  Posted {job.posted_date}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={toggleBookmark}
                className={`p-3 rounded-xl border transition-colors ${
                  saved
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                    : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white'
                }`}
              >
                <Bookmark className={`w-5 h-5 ${saved ? 'fill-amber-400' : ''}`} />
              </button>
              {job.application_url && (
                <a
                  href={job.application_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-600/25 flex items-center gap-2"
                >
                  <span>Apply Now</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-500 font-semibold block mb-1">Salary Range</span>
              <span className="text-emerald-400 font-bold">{job.salary_range || 'Not specified'}</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-500 font-semibold block mb-1">Employment Type</span>
              <span className="text-white font-semibold">{job.employment_type}</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-500 font-semibold block mb-1">Experience Level</span>
              <span className="text-white font-semibold">{job.experience_level}</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-500 font-semibold block mb-1">Min. Experience</span>
              <span className="text-white font-semibold">{job.min_years_experience} Years</span>
            </div>
          </div>

          {/* Skill Gap Direct Action */}
          <div className="p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Target className="w-5 h-5 text-indigo-400" />
              <div>
                <p className="text-xs font-bold text-slate-200">How qualified are you for this position?</p>
                <p className="text-[11px] text-slate-400">Run an instant AI skill gap diagnostic against your profile.</p>
              </div>
            </div>
            <Link
              to={`/dashboard/skill-gap?jobId=${job.id}`}
              className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition-colors"
            >
              Analyze Skill Gap
            </Link>
          </div>

          {/* Skills Required */}
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Required Technical Competencies</h3>
            <div className="flex flex-wrap gap-2">
              {job.required_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-medium text-slate-200"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Complete Job Description</h3>
            <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap bg-slate-950/40 p-6 rounded-2xl border border-slate-800/80">
              {job.description}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
