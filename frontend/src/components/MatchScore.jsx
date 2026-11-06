import React, { useState } from 'react';

const CATEGORY_CONFIG = {
  strong_match: {
    label: 'Strong Match',
    bg: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    dot: 'bg-emerald-500',
    icon: '🎯'
  },
  partial_match: {
    label: 'Partial Match',
    bg: 'bg-blue-50 text-blue-800 border-blue-300',
    dot: 'bg-blue-500',
    icon: '⚡'
  },
  low_match: {
    label: 'Low Match',
    bg: 'bg-amber-50 text-amber-800 border-amber-300',
    dot: 'bg-amber-500',
    icon: '🔍'
  },
  not_eligible: {
    label: 'Not Eligible',
    bg: 'bg-rose-50 text-rose-800 border-rose-300',
    dot: 'bg-rose-500',
    icon: '⛔'
  }
};

export default function MatchScore({
  category,
  skillCoverage,
  isStale = false,
  showCoverage = true,
  size = 'md',
  className = ''
}) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (!category) return null;

  const config = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.low_match;

  const isSmall = size === 'sm';

  return (
    <div className={`relative inline-flex items-center gap-2 ${className}`}>
      {/* Category Pill */}
      <span
        className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${config.bg} ${
          isSmall ? 'text-xs px-2.5 py-0.5' : 'text-xs px-3 py-1 shadow-sm'
        }`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
        <span>{config.icon} {config.label}</span>
      </span>

      {/* Skill Coverage Pill */}
      {showCoverage && skillCoverage !== null && skillCoverage !== undefined && (
        <span
          className={`inline-flex items-center font-medium bg-slate-100 text-slate-700 rounded-full border border-slate-200 ${
            isSmall ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1'
          }`}
          title="Skill coverage percentage"
        >
          Skill coverage: {skillCoverage}%
        </span>
      )}

      {/* Out of Date Indicator */}
      {isStale && (
        <span
          className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300"
          title="Match calculation was based on an earlier version of your profile"
        >
          Out of date
        </span>
      )}

      {/* Info / Tooltip Icon */}
      <div
        className="relative cursor-pointer text-slate-400 hover:text-slate-600 transition-colors"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip(!showTooltip)}
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>

        {/* Floating Tooltip */}
        {showTooltip && (
          <div className="absolute z-30 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2.5 bg-slate-900 text-white text-xs rounded-lg shadow-xl text-center leading-relaxed pointer-events-none">
            This reflects how many required skills you have. It is not a prediction of being hired.
            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900" />
          </div>
        )}
      </div>
    </div>
  );
}

