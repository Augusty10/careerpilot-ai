import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import MatchScore from './MatchScore';
import VerificationBadge from './VerificationBadge';

export default function JobCard({ job, onToggleSave }) {
  const [saving, setSaving] = useState(false);

  const handleSaveClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (saving) return;
    setSaving(true);
    try {
      await onToggleSave(job.job_id, job.is_saved);
    } finally {
      setSaving(false);
    }
  };

  // Fresher status badge configuration
  const getFresherBadge = (status) => {
    switch (status) {
      case 'fresher_friendly':
        return {
          label: '🌱 Fresher Friendly',
          classes: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        };
      case 'entry_level':
        return {
          label: '⚡ Entry Level (0-2 Yrs)',
          classes: 'bg-indigo-50 text-indigo-700 border-indigo-200',
        };
      case 'experience_required':
        return {
          label: '💼 Exp Required (>2 Yrs)',
          classes: 'bg-slate-100 text-slate-600 border-slate-200',
        };
      default:
        return {
          label: '❓ Unclear Experience',
          classes: 'bg-amber-50 text-amber-700 border-amber-200',
        };
    }
  };

  const fresherBadge = getFresherBadge(job.fresher_status);

  // Format posted time
  const formatPosted = (isoString) => {
    if (!isoString) return 'Recently';
    try {
      const date = new Date(isoString);
      const diffDays = Math.floor((new Date() - date) / (1000 * 60 * 60 * 24));
      if (diffDays <= 0) return 'Today';
      if (diffDays === 1) return '1 day ago';
      return `${diffDays} days ago`;
    } catch {
      return 'Recently';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-all p-5 flex flex-col justify-between relative group">
      <div>
        {/* Sample Listing Banner if applicable */}
        {job.is_sample && (
          <div className="mb-3 px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-3xs font-bold uppercase tracking-wider flex items-center gap-1.5">
            <span>⚠️</span>
            <span>Sample listing — not a real vacancy</span>
          </div>
        )}

        {/* Company & Top Actions */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              {job.company}
            </span>
            <Link
              to={`/jobs/${job.job_id}`}
              className="text-base font-bold text-slate-900 hover:text-indigo-600 transition-colors line-clamp-1"
            >
              {job.title}
            </Link>
          </div>

          <button
            onClick={handleSaveClick}
            disabled={saving}
            className={`p-2 rounded-lg border text-sm transition-all ${
              job.is_saved
                ? 'bg-rose-50 border-rose-200 text-rose-600 hover:bg-rose-100'
                : 'bg-slate-50 border-slate-200 text-slate-400 hover:text-slate-700 hover:bg-slate-100'
            }`}
            title={job.is_saved ? 'Remove from Saved Jobs' : 'Save Job'}
          >
            {job.is_saved ? '❤️' : '🤍'}
          </button>
        </div>

        {/* Module 5: Computed Match Category & Skill Coverage */}
        {job.match && (
          <div className="mb-2">
            <MatchScore
              category={job.match.category}
              skillCoverage={job.match.skill_coverage}
              isStale={job.match.is_stale}
              size="sm"
            />
          </div>
        )}

        {/* Badges: Location, Work Mode, Fresher Status & Verification */}
        <div className="flex flex-wrap items-center gap-1.5 my-2.5">
          {job.verification ? (
            <VerificationBadge status={job.verification.overall_status} size="sm" />
          ) : job.is_sample && !job.is_test_scenario ? (
            <VerificationBadge status="not_applicable" size="sm" />
          ) : null}
          <span
            className={`text-2xs font-semibold px-2 py-0.5 rounded-full border ${fresherBadge.classes}`}
          >
            {fresherBadge.label}
          </span>
          <span className="text-2xs font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 capitalize">
            📍 {job.location} ({job.work_mode})
          </span>
          {job.job_type && job.job_type !== 'unknown' && (
            <span className="text-2xs font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 capitalize">
              {job.job_type.replace('_', ' ')}
            </span>
          )}
        </div>

        {/* Experience text & Salary */}
        <div className="text-xs text-slate-600 space-y-1 my-2">
          {job.experience_text && (
            <p className="flex items-center gap-1.5">
              <span className="text-slate-400">Experience:</span>
              <span className="font-medium text-slate-800">{job.experience_text}</span>
            </p>
          )}
          {job.salary_text && (
            <p className="flex items-center gap-1.5">
              <span className="text-slate-400">Compensation:</span>
              <span className="font-semibold text-emerald-700">{job.salary_text}</span>
            </p>
          )}
        </div>

        {/* Skills Preview */}
        {job.required_skills && job.required_skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {job.required_skills.slice(0, 4).map((skill, idx) => (
              <span
                key={idx}
                className="text-2xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium"
              >
                {skill}
              </span>
            ))}
            {job.required_skills.length > 4 && (
              <span className="text-2xs px-1.5 py-0.5 text-slate-400 font-medium">
                +{job.required_skills.length - 4} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Footer / CTA */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        <span className="text-slate-400">
          Posted {formatPosted(job.posted_at)} • via {job.source}
        </span>
        <Link
          to={`/jobs/${job.job_id}`}
          className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          View Details →
        </Link>
      </div>
    </div>
  );
}

