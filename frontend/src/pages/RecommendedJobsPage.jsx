import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import JobCard from '../components/JobCard';
import API from '../services/api';
import { Sparkles, SlidersHorizontal, RefreshCw } from 'lucide-react';

export default function RecommendedJobsPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [minScore, setMinScore] = useState(30);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await API.get(`/recommendations?top_k=12&min_score=${minScore}`);
      setRecommendations(res.data.recommendations || []);
    } catch (err) {
      console.error("Failed to load recommendations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [minScore]);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950">
      <Navbar
        title="Personalized Recommendations"
        subtitle="Ranked by skill match, experience fit, and semantic vector similarity"
      />

      <main className="p-8 max-w-7xl w-full mx-auto space-y-6">
        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-3">
            <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-semibold text-slate-300">Minimum Match Score:</span>
            <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-bold text-xs border border-indigo-500/30">
              {minScore}%
            </span>
            <input
              type="range"
              min="0"
              max="90"
              step="10"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="accent-indigo-500 cursor-pointer w-32"
            />
          </div>

          <button
            onClick={fetchRecommendations}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Matches</span>
          </button>
        </div>

        {/* Content State */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-64 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse"></div>
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-slate-900/60 border border-slate-800">
            <Sparkles className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-base font-bold text-slate-300 mb-1">No recommendations found above {minScore}%</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
              Try lowering the minimum match filter or uploading your resume to update your candidate skills.
            </p>
            <button
              onClick={() => setMinScore(0)}
              className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-semibold text-xs"
            >
              Show All Matches (0%+)
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map((rec) => (
              <JobCard
                key={rec.job.id}
                job={rec.job}
                matchScore={rec.match_score}
                matchingSkills={rec.matching_skills}
                missingSkills={rec.missing_skills}
                matchReasons={rec.match_reasons}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
