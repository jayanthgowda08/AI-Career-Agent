import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import JobCard from '../components/JobCard';
import API from '../services/api';
import { Bookmark, Sparkles } from 'lucide-react';

export default function SavedJobsPage() {
  const [savedRecords, setSavedRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchSaved = async () => {
    setLoading(true);
    try {
      const res = await API.get('/agent/saved-jobs');
      setSavedRecords(res.data || []);
    } catch (err) {
      console.error("Failed to load saved jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSaved();
  }, []);

  const handleBookmarkToggle = (jobId, isSaved) => {
    if (!isSaved) {
      setSavedRecords((prev) => prev.filter((r) => r.job.id !== jobId));
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950">
      <Navbar
        title="Saved Opportunities"
        subtitle="Your bookmarked jobs and tracked applications"
      />

      <main className="p-8 max-w-7xl w-full mx-auto space-y-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse"></div>
            ))}
          </div>
        ) : savedRecords.length === 0 ? (
          <div className="p-16 text-center rounded-3xl bg-slate-900/60 border border-slate-800 max-w-md mx-auto mt-10">
            <Bookmark className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-base font-bold text-slate-300 mb-1">No Saved Jobs Yet</h3>
            <p className="text-xs text-slate-500 mb-6">
              Click the bookmark icon on any job card or tell your AI assistant to save a role for you.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {savedRecords.map((r) => (
              <JobCard
                key={r.id}
                job={r.job}
                isSaved={true}
                onBookmarkToggle={handleBookmarkToggle}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
