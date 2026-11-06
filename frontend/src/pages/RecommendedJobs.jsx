import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { matchingAPI } from '../services/api';
import MatchScore from '../components/MatchScore';

export default function RecommendedJobs() {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({ strong_match: 0, partial_match: 0, low_match: 0, not_eligible: 0 });
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  // Filters
  const [activeCategory, setActiveCategory] = useState(''); // '' = all
  const [hideNotEligible, setHideNotEligible] = useState(true);
  const [sortBy, setSortBy] = useState('rank'); // 'rank', 'coverage', 'recent'

  useEffect(() => {
    fetchRecommended();
  }, [activeCategory, hideNotEligible, sortBy]);

  const fetchRecommended = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const params = {
        exclude_not_eligible: hideNotEligible,
        sort_by: sortBy,
        limit: 30
      };
      if (activeCategory) {
        params.category = activeCategory;
      }
      const res = await matchingAPI.getRecommendedJobs(params);
      if (res.data?.jobs) {
        setJobs(res.data.jobs);
        if (res.data.stats) {
          setStats(res.data.stats);
        }
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Failed to load recommended jobs.');
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { id: '', label: 'All Recommended', count: (stats.strong_match || 0) + (stats.partial_match || 0) + (stats.low_match || 0) },
    { id: 'strong_match', label: '🎯 Strong Match', count: stats.strong_match || 0 },
    { id: 'partial_match', label: '⚡ Partial Match', count: stats.partial_match || 0 },
    { id: 'low_match', label: '🔍 Low Match', count: stats.low_match || 0 },
  ];

  if (!hideNotEligible) {
    categories.push({ id: 'not_eligible', label: '⛔ Not Eligible', count: stats.not_eligible || 0 });
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="inline-flex items-center gap-2 text-indigo-600 font-bold text-xs uppercase tracking-wider mb-1">
            <span>✨</span>
            <span>Module 5: Personalized Matching</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Recommended Opportunities For You
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Ranked deterministically by alignment with your verified Master Career Profile.
          </p>
        </div>

        {/* Disclaimer / Notice Pill */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-500 max-w-sm">
          💡 <strong>Notice:</strong> Match score reflects skill & criteria coverage. It is an objective fit assessment, not a hiring prediction.
        </div>
      </div>

      {/* Controls Bar: Filter Tabs & Toggles */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm mb-6 flex flex-wrap items-center justify-between gap-4">
        {/* Category Tabs */}
        <div className="flex flex-wrap gap-1.5" id="recommended-category-tabs">
          {categories.map((cat) => {
            const isActive = activeCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200'
                }`}
              >
                <span>{cat.label}</span>
                <span className={`text-2xs px-1.5 py-0.2 rounded-full ${isActive ? 'bg-indigo-700 text-white' : 'bg-slate-200 text-slate-600'}`}>
                  {cat.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Right side controls: Hide not eligible toggle & sort */}
        <div className="flex items-center gap-4 text-xs text-slate-700">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              id="toggle-hide-not-eligible"
              checked={hideNotEligible}
              onChange={(e) => setHideNotEligible(e.target.checked)}
              className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500"
            />
            <span className="font-medium">Hide Not Eligible</span>
          </label>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="rank">Best Match (Category Rank)</option>
              <option value="coverage">Skill Coverage %</option>
              <option value="recent">Most Recent</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error state */}
      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-xs text-rose-700 mb-6 flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={fetchRecommended} className="font-bold underline hover:text-rose-900">
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="py-20 text-center">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">Calculating your personalized match recommendations...</p>
          <p className="text-xs text-slate-400 mt-1">Comparing technical skills, education, and experience</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-sm">
          <div className="text-4xl mb-3">🔍</div>
          <h3 className="text-base font-bold text-slate-900 mb-1">No Matching Opportunities Found</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mb-5">
            No active jobs match the selected filter criteria. Try toggling off "Hide Not Eligible" or discovering more jobs.
          </p>
          <Link
            to="/jobs"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <span>Explore All Jobs</span>
            <span>→</span>
          </Link>
        </div>
      ) : (
        /* Ranked Jobs Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="recommended-jobs-grid">
          {jobs.map(({ job, match }) => (
            <div
              key={job.job_id}
              className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                {/* Sample badge */}
                {job.is_sample && (
                  <div className="mb-2 px-2 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-800 text-3xs font-bold uppercase tracking-wider inline-block">
                    ⚠️ Sample Listing
                  </div>
                )}

                {/* Match Score Badge */}
                <div className="mb-3">
                  <MatchScore
                    category={match.category}
                    skillCoverage={match.skill_coverage}
                    isStale={match.is_stale}
                    size="md"
                  />
                </div>

                {/* Title & Company */}
                <h3 className="text-base font-bold text-slate-900 line-clamp-1 hover:text-indigo-600 transition-colors">
                  <Link to={`/jobs/${job.job_id}`}>{job.title}</Link>
                </h3>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-0.5">
                  {job.company}
                </p>

                {/* Location & Mode */}
                <div className="flex flex-wrap items-center gap-1.5 mt-2.5 text-2xs text-slate-600">
                  <span className="px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200">
                    📍 {job.location} ({job.work_mode})
                  </span>
                  {job.fresher_status && (
                    <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {job.fresher_status.replace('_', ' ')}
                    </span>
                  )}
                </div>

                {/* Matched vs Missing Skills Preview */}
                <div className="mt-3.5 space-y-1.5 text-xs">
                  {match.matched_skills && match.matched_skills.length > 0 && (
                    <div className="flex items-start gap-1.5 text-emerald-800">
                      <span className="font-semibold text-2xs shrink-0 mt-0.5">Matched:</span>
                      <span className="line-clamp-1 text-2xs">{match.matched_skills.join(', ')}</span>
                    </div>
                  )}
                  {match.missing_skills && match.missing_skills.length > 0 && (
                    <div className="flex items-start gap-1.5 text-rose-700">
                      <span className="font-semibold text-2xs shrink-0 mt-0.5">Missing:</span>
                      <span className="line-clamp-1 text-2xs">{match.missing_skills.join(', ')}</span>
                    </div>
                  )}
                </div>

                {/* Analysis Preview */}
                {match.explanation && (
                  <p className="text-xs text-slate-600 mt-3 line-clamp-2 bg-slate-50 p-2 rounded-lg border border-slate-100 leading-relaxed italic">
                    "{match.explanation}"
                  </p>
                )}
              </div>

              {/* Card Footer CTA */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-2xs text-slate-400">
                  {job.experience_text || 'Fresher friendly'}
                </span>
                <Link
                  to={`/jobs/${job.job_id}`}
                  className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1"
                >
                  <span>View Breakdown</span>
                  <span>→</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

