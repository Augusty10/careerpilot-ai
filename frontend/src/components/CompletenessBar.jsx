import React from 'react';

export const CompletenessBar = ({ percentage = 0, status = 'draft' }) => {
  const isApproved = status === 'approved';

  const getColor = () => {
    if (isApproved) return 'bg-emerald-500';
    if (percentage >= 80) return 'bg-emerald-500';
    if (percentage >= 40) return 'bg-indigo-600';
    return 'bg-amber-500';
  };

  return (
    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Profile Strength
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              isApproved
                ? 'bg-emerald-100 text-emerald-800'
                : 'bg-amber-100 text-amber-800'
            }`}
          >
            {isApproved ? 'Approved Master' : 'Draft In Progress'}
          </span>
        </div>
        <span className="text-sm font-extrabold text-slate-900">
          {percentage}%
        </span>
      </div>

      <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ease-out rounded-full ${getColor()}`}
          style={{ width: `${Math.min(100, Math.max(5, percentage))}%` }}
        />
      </div>

      <div className="mt-2 text-xs text-slate-500 flex justify-between">
        <span>
          {isApproved
            ? '✅ Master profile ready for AI resume generation'
            : percentage >= 80
            ? 'Almost ready! Review and click "Approve"'
            : 'Fill required sections or upload your resume to reach 100%'}
        </span>
      </div>
    </div>
  );
};

export default CompletenessBar;

