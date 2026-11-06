import React, { useState, useEffect } from 'react';
import { jobAPI, profileAPI } from '../services/api';
import JobCard from '../components/JobCard';

export default function JobDiscovery() {
  const [activeTab, setActiveTab] = useState('all'); // 'all' or 'saved'
  const [jobs, setJobs] = useState([]);
  const [savedJobs, setSavedJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [discoverySummary, setDiscoverySummary] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [workModeFilter, setWorkModeFilter] = useState('all');
  const [fresherOnly, setFresherOnly] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);
  const [fresherCount, setFresherCount] = useState(0);

  // Predefined role chips
  const roleOptions = [
    'All Roles',
    'Full Stack',
    'Python',
    'Frontend',
    'Data Analyst',
    'QA / Automation',
    'Cybersecurity',
    'DevOps',
  ];

  useEffect(() => {
    loadJobs();
    loadSavedJobs();
  }, [page, roleFilter, workModeFilter, fresherOnly]);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        limit: 12,
        fresher_only: fresherOnly,
        exclude_expired: true,
      };

      if (roleFilter !== 'all' && roleFilter !== 'All Roles') {
        params.role = roleFilter;
      }
      if (workModeFilter !== 'all') {
        params.work_mode = workModeFilter;
      }
      if (search.trim()) {
        params.search = search.trim();
      }

      const res = await jobAPI.listJobs(params);
      if (res.data) {
        setJobs(res.data.jobs || []);
        setTotalPages(res.data.pages || 1);
        setTotalJobs(res.data.total || 0);
        setFresherCount(res.data.fresher_friendly_count || 0);
      }
    } catch (err) {
      console.error('Failed to load jobs feed:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSavedJobs = async () => {
    try {
      const res = await jobAPI.getSavedJobs();
      if (res.data?.saved_jobs) {
        setSavedJobs(res.data.saved_jobs);
      }
    } catch (err) {
      console.error('Failed to load saved jobs:', err);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadJobs();
  };

  const handleRunDiscovery = async () => {
    setDiscovering(true);
    setDiscoverySummary(null);
    try {
      const res = await jobAPI.discoverJobs({});
      if (res.data?.summary) {
        setDiscoverySummary(res.data.summary);
      }
      setPage(1);
      await loadJobs();
      await loadSavedJobs();
    } catch (err) {
      alert(`Discovery failed: ${err.response?.data?.message || err.message}`);
    } finally {
      setDiscovering(false);
    }
  };

  const handleToggleSave = async (jobId, isCurrentlySaved) => {
    try {
      if (isCurrentlySaved) {
        await jobAPI.unsaveJob(jobId);
      } else {
        await jobAPI.saveJob(jobId);
      }

      // Optimistically update lists
      setJobs((prev) =>
        prev.map((j) => (j.job_id === jobId ? { ...j, is_saved: !isCurrentlySaved } : j))
      );
      await loadSavedJobs();
    } catch (err) {
      alert(`Failed to update save status: ${err.message}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            AI Job Discovery
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Aggregated entry-level tech opportunities from authorized sources. Zero scraping, zero ghost jobs.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-3">
          <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 text-center">
            <span className="text-xl font-bold text-indigo-600 block leading-none">
              {totalJobs}
            </span>
            <span className="text-3xs uppercase tracking-wider text-slate-500 font-semibold">
              Available Jobs
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 text-center">
            <span className="text-xl font-bold text-emerald-600 block leading-none">
              {fresherCount}
            </span>
            <span className="text-3xs uppercase tracking-wider text-slate-500 font-semibold">
              Fresher Friendly
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 text-center">
            <span className="text-xl font-bold text-rose-600 block leading-none">
              {savedJobs.length}
            </span>
            <span className="text-3xs uppercase tracking-wider text-slate-500 font-semibold">
              Saved Jobs
            </span>
          </div>
        </div>
      </div>

      {/* Discovery Action Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Discover Job Opportunities
            </h2>
            <p className="text-xs text-slate-500">
              Scans enabled sources (Curated Sample Seed & Official APIs) to find entry-level openings.
            </p>
          </div>

          <button
            id="btn-discover-jobs"
            onClick={handleRunDiscovery}
            disabled={discovering}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-semibold text-xs rounded-xl shadow-sm transition-all flex items-center justify-center gap-2"
          >
            {discovering ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span>Searching & Normalizing Jobs...</span>
              </>
            ) : (
              <span>🔍 Find Jobs</span>
            )}
          </button>
        </div>

        {/* Discovery Summary Alert */}
        {discoverySummary && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-xl text-xs space-y-1">
            <div className="flex items-center gap-2 font-bold text-emerald-800">
              <span>✅</span>
              <span>Discovery run completed successfully!</span>
            </div>
            <p className="text-emerald-700">
              Found <strong>{discoverySummary.fetched}</strong> jobs • Stored/updated{' '}
              <strong>{discoverySummary.stored}</strong> • Flagged{' '}
              <strong>{discoverySummary.duplicates_flagged}</strong> duplicates • Filtered{' '}
              <strong>{discoverySummary.expired_flagged}</strong> expired postings.
            </p>
          </div>
        )}
      </div>

      {/* Navigation View Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-200">
        <button
          onClick={() => setActiveTab('all')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'all'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          All Vacancies ({totalJobs})
        </button>
        <button
          onClick={() => setActiveTab('saved')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'saved'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Saved Jobs ({savedJobs.length})
        </button>
        <Link
          to="/jobs/recommended"
          className="pb-3 text-sm font-semibold border-b-2 border-transparent text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5 ml-auto transition-colors"
        >
          <span>🎯</span>
          <span>Recommended For You →</span>
        </Link>
      </div>

      {/* All Jobs View with Filters */}
      {activeTab === 'all' && (
        <div className="space-y-6">
          {/* Filter Bar */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              {/* Search input */}
              <form onSubmit={handleSearchSubmit} className="flex-1 w-full">
                <div className="relative">
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by title, company, or skills (e.g. Python, React)..."
                    className="w-full text-xs rounded-lg border border-slate-300 pl-3 pr-20 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="absolute right-1.5 top-1.5 bottom-1.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 text-2xs font-semibold rounded-md transition-colors"
                  >
                    Search
                  </button>
                </div>
              </form>

              {/* Work Mode & Fresher toggle */}
              <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
                <select
                  value={workModeFilter}
                  onChange={(e) => {
                    setWorkModeFilter(e.target.value);
                    setPage(1);
                  }}
                  className="text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="all">Work Mode: All</option>
                  <option value="remote">Remote Only</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">On-Site</option>
                </select>

                <label className="inline-flex items-center gap-2 cursor-pointer bg-slate-50 px-3 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700">
                  <input
                    type="checkbox"
                    checked={fresherOnly}
                    onChange={(e) => {
                      setFresherOnly(e.target.checked);
                      setPage(1);
                    }}
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Fresher Friendly Only</span>
                </label>
              </div>
            </div>

            {/* Quick Role Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100">
              <span className="text-2xs font-bold text-slate-400 uppercase tracking-wider mr-1">
                Roles:
              </span>
              {roleOptions.map((opt) => (
                <button
                  key={opt}
                  onClick={() => {
                    setRoleFilter(opt === 'All Roles' ? 'all' : opt);
                    setPage(1);
                  }}
                  className={`text-2xs font-semibold px-2.5 py-1 rounded-md transition-all ${
                    (opt === 'All Roles' && roleFilter === 'all') || roleFilter === opt
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          {/* Jobs Feed Grid */}
          {loading ? (
            <div className="p-16 text-center text-slate-400">Loading vacancies...</div>
          ) : jobs.length === 0 ? (
            <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center space-y-3">
              <span className="text-4xl block">🔍</span>
              <h3 className="text-base font-bold text-slate-800">No matching jobs found</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Try adjusting your filters or click "Find Jobs" above to discover fresh opportunities.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {jobs.map((job) => (
                <JobCard key={job.job_id} job={job} onToggleSave={handleToggleSave} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-200 text-xs">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 rounded-lg border border-slate-300 disabled:opacity-40 font-semibold text-slate-700 hover:bg-slate-50"
              >
                ← Previous
              </button>
              <span className="text-slate-500">
                Page <strong>{page}</strong> of <strong>{totalPages}</strong>
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1.5 rounded-lg border border-slate-300 disabled:opacity-40 font-semibold text-slate-700 hover:bg-slate-50"
              >
                Next →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Saved Jobs View */}
      {activeTab === 'saved' && (
        <div className="space-y-6">
          {savedJobs.length === 0 ? (
            <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center space-y-3">
              <span className="text-4xl block">❤️</span>
              <h3 className="text-base font-bold text-slate-800">No saved jobs yet</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Bookmark interesting vacancies by clicking the heart icon on any job card.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {savedJobs.map((job) => (
                <JobCard key={job.job_id} job={job} onToggleSave={handleToggleSave} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
