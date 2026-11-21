import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  MapPin,
  Building,
  DollarSign,
  Bookmark,
  CheckCircle2,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import API from '../services/api';

export default function JobCard({ job, matchScore, matchingSkills, missingSkills, matchReasons, isSaved: initialSaved = false, onBookmarkToggle }) {
  const [saved, setSaved] = useState(initialSaved);
  const [saving, setSaving] = useState(false);

  const toggleBookmark = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setSaving(true);
    try {
      if (saved) {
        await API.delete(`/agent/saved-jobs/${job.id}`);
        setSaved(false);
      } else {
        await API.post(`/agent/saved-jobs/${job.id}`);
        setSaved(true);
      }
      if (onBookmarkToggle) onBookmarkToggle(job.id, !saved);
    } catch (err) {
      console.error("Bookmark toggle failed:", err);
    } finally {
      setSaving(false);
    }
  };

  const getBadgeColor = (score) => {
    if (score >= 80) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
    if (score >= 60) return 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30';
    if (score >= 40) return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    return 'bg-slate-700 text-slate-300 border-slate-600';
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 hover:border-indigo-500/40 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/5 group flex flex-col justify-between">
      <div>
        {/* Header Row */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <h3 className="text-base font-bold text-slate-100 group-hover:text-indigo-400 transition-colors">
              {job.title}
            </h3>
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
              <span className="flex items-center gap-1 font-medium text-slate-300">
                <Building className="w-3.5 h-3.5 text-slate-500" />
                {job.company}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                {job.location}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {matchScore !== undefined && (
              <div className={`px-2.5 py-1 rounded-full text-xs font-bold border flex items-center gap-1 ${getBadgeColor(matchScore)}`}>
                <Sparkles className="w-3 h-3" />
                <span>{matchScore}% Match</span>
              </div>
            )}
            <button
              onClick={toggleBookmark}
              disabled={saving}
              className={`p-2 rounded-xl border transition-colors ${
                saved
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                  : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-white'
              }`}
            >
              <Bookmark className={`w-4 h-4 ${saved ? 'fill-amber-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Snippet */}
        <p className="text-xs text-slate-400 line-clamp-2 mb-4 leading-relaxed">
          {job.description}
        </p>

        {/* Badges / Compensation */}
        <div className="flex flex-wrap items-center gap-2 mb-4 text-[11px]">
          {job.salary_range && (
            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20 flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              {job.salary_range}
            </span>
          )}
          <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
            {job.employment_type}
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
            {job.experience_level}
          </span>
        </div>

        {/* Skills Tag Cloud */}
        {job.required_skills && job.required_skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {job.required_skills.slice(0, 5).map((skill, idx) => {
              const isMatched = matchingSkills && matchingSkills.includes(skill);
              return (
                <span
                  key={idx}
                  className={`text-[10px] px-2 py-0.5 rounded-md font-medium border ${
                    isMatched
                      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                      : 'bg-slate-800/60 text-slate-400 border-slate-750'
                  }`}
                >
                  {skill}
                </span>
              );
            })}
            {job.required_skills.length > 5 && (
              <span className="text-[10px] px-1.5 py-0.5 text-slate-500 font-medium">
                +{job.required_skills.length - 5} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Footer link to Job Details & Gap Analysis */}
      <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
        <Link
          to={`/dashboard/skill-gap?jobId=${job.id}`}
          className="text-slate-400 hover:text-indigo-400 transition-colors font-medium flex items-center gap-1"
        >
          Check Skill Gap
        </Link>

        <Link
          to={`/dashboard/jobs/${job.id}`}
          className="inline-flex items-center gap-1 font-semibold text-indigo-400 hover:text-indigo-300 group-hover:translate-x-0.5 transition-all"
        >
          <span>View Details</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
