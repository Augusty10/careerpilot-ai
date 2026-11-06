import React, { useState } from 'react';
import MatchScore from './MatchScore';

export default function MatchBreakdown({
  match,
  onRecompute,
  recomputing = false
}) {
  if (!match) return null;

  const {
    category,
    skill_coverage,
    skills = {},
    education = {},
    graduation_year = {},
    experience = {},
    location = {},
    job_type = {},
    certifications = {},
    hard_failures = [],
    warnings = [],
    explanation = '',
    is_stale = false,
    disclaimer
  } = match;

  const matchedSkills = skills.matched || [];
  const relatedSkills = skills.related || [];
  const missingSkills = skills.missing || [];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'meets':
      case 'meets_stated_requirement':
      case 'match':
      case 'remote':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
            ✓ Meets
          </span>
        );
      case 'does_not_meet':
      case 'below_requirement':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800">
            ✕ Below Req
          </span>
        );
      case 'mismatch':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
            ⚠ Mismatch
          </span>
        );
      case 'unclear':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">
            ? Unclear
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-600">
            Not Stated
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden my-6">
      {/* Header Banner */}
      <div className="bg-slate-50 border-b border-slate-200 p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-bold text-slate-900">Job Match & Eligibility Breakdown</h3>
            <MatchScore
              category={category}
              skillCoverage={skill_coverage}
              isStale={is_stale}
              size="md"
            />
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {disclaimer || 'This reflects how many required skills you have. It is not a prediction of being hired.'}
          </p>
        </div>

        {onRecompute && (
          <button
            onClick={onRecompute}
            disabled={recomputing}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-lg border transition-colors inline-flex items-center gap-1.5 ${
              is_stale
                ? 'bg-amber-600 hover:bg-amber-700 text-white border-amber-600 shadow-sm'
                : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-300'
            } disabled:opacity-50`}
          >
            <svg
              className={`w-3.5 h-3.5 ${recomputing ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>{recomputing ? 'Recomputing...' : is_stale ? 'Recompute Match (Profile Changed)' : 'Recompute Match'}</span>
          </button>
        )}
      </div>

      {/* Out of Date Alert Box */}
      {is_stale && (
        <div className="bg-amber-50 border-b border-amber-200 px-5 py-3 flex items-center justify-between text-xs text-amber-800">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-amber-600 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span><strong>Notice:</strong> Your master profile has changed since this match was calculated. Recompute to view updated alignment.</span>
          </div>
          {onRecompute && (
            <button
              onClick={onRecompute}
              disabled={recomputing}
              className="font-bold underline hover:text-amber-950 ml-3 shrink-0"
            >
              Recompute now
            </button>
          )}
        </div>
      )}

      {/* Plain Language Explanation */}
      {explanation && (
        <div className="p-5 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0 mt-0.5">
              💡
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-800 uppercase tracking-wider">Analysis Summary</h4>
              <p className="text-sm text-slate-700 mt-1 leading-relaxed">{explanation}</p>
            </div>
          </div>
        </div>
      )}

      {/* Hard Ineligibility Failures */}
      {hard_failures && hard_failures.length > 0 && (
        <div className="p-5 border-b border-rose-100 bg-rose-50/60">
          <h4 className="text-xs font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1.5">
            <span>⛔ Minimum Eligibility Requirements Not Met</span>
          </h4>
          <ul className="mt-2 space-y-1.5 text-xs text-rose-700 list-disc list-inside">
            {hard_failures.map((fail, idx) => (
              <li key={idx} className="leading-relaxed">{fail}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings List */}
      {warnings && warnings.length > 0 && (
        <div className="p-4 border-b border-amber-100 bg-amber-50/50 text-xs text-amber-800 space-y-1">
          {warnings.map((warn, idx) => (
            <div key={idx} className="flex items-start gap-1.5">
              <span>⚠</span>
              <span>{warn}</span>
            </div>
          ))}
        </div>
      )}

      {/* Requirement Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-600 border-collapse">
          <thead>
            <tr className="bg-slate-100/75 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider">
              <th className="py-3 px-4 w-1/4">Requirement</th>
              <th className="py-3 px-4 w-1/3">Job Needs</th>
              <th className="py-3 px-4 w-1/4">You Have</th>
              <th className="py-3 px-4 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {/* Technical Skills Row */}
            <tr className="hover:bg-slate-50/50">
              <td className="py-3 px-4 font-semibold text-slate-900">
                Technical Skills
                {skill_coverage !== null && (
                  <div className="text-[11px] font-normal text-slate-500 mt-0.5">
                    {skill_coverage}% coverage
                  </div>
                )}
              </td>
              <td className="py-3 px-4">
                {skills.raw_job_skills && skills.raw_job_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {skills.raw_job_skills.map((s, idx) => (
                      <span key={idx} className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-700 border border-slate-200">
                        {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-slate-400 italic">None specified</span>
                )}
              </td>
              <td className="py-3 px-4">
                <div className="space-y-1">
                  {matchedSkills.length > 0 && (
                    <div className="text-emerald-700">
                      <span className="font-medium text-[11px]">Exact matches: </span>
                      {matchedSkills.join(', ')}
                    </div>
                  )}
                  {relatedSkills.length > 0 && (
                    <div className="text-blue-700">
                      <span className="font-medium text-[11px]">Related: </span>
                      {relatedSkills.map(r => `${r.candidate_skill} for ${r.job_skill}`).join(', ')}
                    </div>
                  )}
                  {missingSkills.length > 0 && (
                    <div className="text-rose-700">
                      <span className="font-medium text-[11px]">Missing: </span>
                      {missingSkills.join(', ')}
                    </div>
                  )}
                </div>
              </td>
              <td className="py-3 px-4 text-center">
                {category === 'strong_match' ? getStatusBadge('meets') :
                 category === 'partial_match' ? getStatusBadge('meets') :
                 category === 'low_match' ? getStatusBadge('mismatch') : getStatusBadge('does_not_meet')}
              </td>
            </tr>

            {/* Education Row */}
            <tr className="hover:bg-slate-50/50">
              <td className="py-3 px-4 font-semibold text-slate-900">Education</td>
              <td className="py-3 px-4">{education.job_requirement || 'Not specified'}</td>
              <td className="py-3 px-4">{education.candidate_value || 'None listed'}</td>
              <td className="py-3 px-4 text-center">{getStatusBadge(education.status)}</td>
            </tr>

            {/* Batch Year Row */}
            <tr className="hover:bg-slate-50/50">
              <td className="py-3 px-4 font-semibold text-slate-900">Graduation Year</td>
              <td className="py-3 px-4">{graduation_year.job_requirement || 'Not specified'}</td>
              <td className="py-3 px-4">{graduation_year.candidate_value ? `Batch ${graduation_year.candidate_value}` : 'Not listed'}</td>
              <td className="py-3 px-4 text-center">{getStatusBadge(graduation_year.status)}</td>
            </tr>

            {/* Experience Row */}
            <tr className="hover:bg-slate-50/50">
              <td className="py-3 px-4 font-semibold text-slate-900">Experience</td>
              <td className="py-3 px-4">{experience.job_requirement || 'Not specified'}</td>
              <td className="py-3 px-4">{experience.candidate_value || 'Fresher'}</td>
              <td className="py-3 px-4 text-center">{getStatusBadge(experience.status)}</td>
            </tr>

            {/* Location Row */}
            <tr className="hover:bg-slate-50/50">
              <td className="py-3 px-4 font-semibold text-slate-900">Location & Mode</td>
              <td className="py-3 px-4">{location.job_requirement || 'Unspecified'}</td>
              <td className="py-3 px-4">
                {Array.isArray(location.candidate_value)
                  ? location.candidate_value.join(', ') || 'Any'
                  : String(location.candidate_value || 'Any')}
              </td>
              <td className="py-3 px-4 text-center">{getStatusBadge(location.status)}</td>
            </tr>

            {/* Certifications Row */}
            {certifications.job_requirement && (
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-semibold text-slate-900">Certifications</td>
                <td className="py-3 px-4">{certifications.job_requirement}</td>
                <td className="py-3 px-4">
                  {certifications.missing && certifications.missing.length > 0 ? (
                    <span className="text-rose-600">Missing: {certifications.missing.join(', ')}</span>
                  ) : (
                    <span className="text-emerald-600">All satisfied</span>
                  )}
                </td>
                <td className="py-3 px-4 text-center">{getStatusBadge(certifications.status)}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Closing the Gap Advice Card */}
      {missingSkills.length > 0 && category !== 'not_eligible' && (
        <div className="p-5 bg-indigo-50/30 border-t border-slate-100">
          <h4 className="text-xs font-semibold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
            <span>🎯 How to Close the Gap for this Role</span>
          </h4>
          <p className="text-xs text-slate-600 mt-1">
            Focus on learning or building a small project with <strong>{missingSkills.slice(0, 3).join(', ')}</strong> to strengthen your application profile.
          </p>
        </div>
      )}
    </div>
  );
}

