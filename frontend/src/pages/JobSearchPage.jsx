import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import JobCard from '../components/JobCard';
import API from '../services/api';
import { Search, MapPin, Briefcase, Sparkles, Filter, AlertCircle } from 'lucide-react';

export default function JobSearchPage() {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [searchMode, setSearchMode] = useState('hybrid'); // 'hybrid' or 'semantic'
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(null);

  const performSearch = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (query.trim()) {
        const endpoint = searchMode === 'hybrid' ? '/search/hybrid' : '/search/semantic';
        const res = await API.post(endpoint, {
          query,
          location: location || undefined,
          top_k: 15,
        });
        const items = res.data?.results || [];
        setJobs(items.map((r) => ({ ...r.job, matchScore: intScore(r.similarity_score) })));
        setTotal(res.data?.total_results ?? items.length);
      } else {
        const res = await API.get('/jobs', {
          params: { location: location || undefined, page_size: 15 },
        });
        const jobList = res.data?.jobs;
        if (Array.isArray(jobList)) {
          setJobs(jobList);
          setTotal(res.data?.total ?? jobList.length);
        } else {
          setJobs([]);
          setTotal(0);
        }
      }
    } catch (err) {
      console.error("Search failed:", err);
      setError("Unable to connect to backend server. Render's free web service may be waking up from sleep. Please wait ~20 seconds and click Search again.");
    } finally {
      setLoading(false);
    }
  };

  const intScore = (score) => Math.round(score * 100);

  useEffect(() => {
    performSearch();
  }, []);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950">
      <Navbar
        title="Explore Opportunities"
        subtitle="Semantic vector search using pgvector cosine distance + keyword fusion"
      />

      <main className="p-8 max-w-7xl w-full mx-auto space-y-6">
        {/* Error Notice */}
        {error && (
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
              <span>{error}</span>
            </div>
            <button
              onClick={performSearch}
              className="px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 font-bold shrink-0 text-amber-200 transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Search controls */}
        <form onSubmit={performSearch} className="p-4 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-6 relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by natural language query (e.g. 'building neural networks with PyTorch')..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="md:col-span-3 relative">
              <MapPin className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Location (e.g. 'Remote', 'Seattle')"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="md:col-span-3 flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-sm text-white shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2"
              >
                <Search className="w-4 h-4" />
                <span>Search</span>
              </button>
            </div>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-4 pt-2 border-t border-slate-800/80 text-xs text-slate-400">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-indigo-400" />
              Search Engine:
            </span>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                name="mode"
                checked={searchMode === 'hybrid'}
                onChange={() => setSearchMode('hybrid')}
                className="accent-indigo-500"
              />
              <span>Hybrid Search (Semantic 60% + Keyword 40%)</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                name="mode"
                checked={searchMode === 'semantic'}
                onChange={() => setSearchMode('semantic')}
                className="accent-indigo-500"
              />
              <span>Pure pgvector Semantic Search</span>
            </label>
          </div>
        </form>

        {/* Results Header */}
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>Found {total} opportunities</span>
          {query && <span className="text-indigo-400 font-medium">Ranked by semantic relevance to "{query}"</span>}
        </div>

        {/* Job Cards Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-64 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse"></div>
            ))}
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-slate-900/60 border border-slate-800">
            <Briefcase className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-base font-bold text-slate-300 mb-1">No jobs match your search criteria</h3>
            <p className="text-xs text-slate-500">Try broadening your keywords or removing the location filter.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                matchScore={job.matchScore}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
