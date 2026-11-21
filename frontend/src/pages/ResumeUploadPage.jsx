import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import API from '../services/api';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Sparkles, ArrowRight } from 'lucide-react';

export default function ResumeUploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Only PDF resumes are supported.');
        setFile(null);
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await API.post('/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data.parsed_data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Resume upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950">
      <Navbar
        title="Resume Upload & Analysis"
        subtitle="Extract technical skills and work history with Gemini 1.5 Flash structured schemas"
      />

      <main className="p-8 max-w-4xl w-full mx-auto space-y-6">
        {/* Upload Form */}
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-6">
          <div>
            <h2 className="text-base font-bold text-white mb-1">Upload Your PDF Resume</h2>
            <p className="text-xs text-slate-400">
              Our dual extraction pipeline parses your PDF and structures your skills, experiences, and education directly into your profile.
            </p>
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleUpload} className="space-y-4">
            <label className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-3xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-950/40 group">
              <UploadCloud className="w-10 h-10 text-slate-500 group-hover:text-indigo-400 transition-colors mb-3" />
              <span className="text-sm font-semibold text-slate-200">
                {file ? file.name : 'Click to select or drag and drop your PDF resume'}
              </span>
              <span className="text-xs text-slate-500 mt-1">PDF documents only (up to 10 MB)</span>
              <input type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
            </label>

            <button
              type="submit"
              disabled={!file || uploading}
              className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-sm shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Extracting text & reasoning with Gemini...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Analyze & Update Profile</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Extraction Preview Result */}
        {result && (
          <div className="p-8 rounded-3xl bg-slate-900 border border-emerald-500/30 shadow-2xl space-y-6">
            <div className="flex items-center gap-3 text-emerald-400">
              <CheckCircle2 className="w-6 h-6" />
              <h2 className="text-lg font-bold text-white">Extraction Successful! Candidate Profile Updated</h2>
            </div>

            {/* Extracted Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <span className="font-bold text-slate-400 uppercase tracking-wider block">Candidate Info</span>
                <p className="text-sm font-bold text-white">{result.full_name || 'Name not detected'}</p>
                <p className="text-slate-300">{result.headline || 'Software Engineer'}</p>
                <p className="text-slate-400">{result.location}</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <span className="font-bold text-slate-400 uppercase tracking-wider block">Suggested Target Roles</span>
                <div className="flex flex-wrap gap-1.5">
                  {result.suggested_roles?.map((r, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-md bg-indigo-500/15 text-indigo-300 font-semibold border border-indigo-500/20">
                      {r}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Extracted Skills */}
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Technical Skills Detected</h3>
              <div className="flex flex-wrap gap-1.5">
                {result.technical_skills?.map((s, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-md bg-emerald-500/15 text-emerald-300 font-semibold border border-emerald-500/25">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            {/* Extracted Experience */}
            {result.experience && result.experience.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Work Experience</h3>
                <div className="space-y-3">
                  {result.experience.map((exp, i) => (
                    <div key={i} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                      <p className="font-bold text-slate-200">{exp.title} • {exp.company}</p>
                      <p className="text-slate-500 text-[11px] mb-1">{exp.start_date} - {exp.end_date}</p>
                      <p className="text-slate-400">{exp.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
