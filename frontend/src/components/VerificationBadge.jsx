import React from 'react';

/**
 * VerificationBadge Component for CareerPilot AI (Module 6).
 * Renders distinct accessible status badges with both visual icons and descriptive text labels.
 */
export default function VerificationBadge({ status, size = 'sm', className = '' }) {
  const getBadgeConfig = (st) => {
    switch (st) {
      case 'corroborated':
        return {
          icon: '🛡️',
          label: 'Corroborated',
          classes: 'bg-emerald-50 text-emerald-800 border-emerald-300 ring-1 ring-emerald-200/50',
          desc: 'Available evidence supports this posting',
        };
      case 'suspicious':
        return {
          icon: '🚨',
          label: 'Suspicious',
          classes: 'bg-rose-50 text-rose-800 border-rose-300 ring-1 ring-rose-200/50 font-bold animate-pulse',
          desc: 'Critical warning indicators detected',
        };
      case 'not_applicable':
        return {
          icon: 'ℹ️',
          label: 'Not applicable (sample listing)',
          classes: 'bg-slate-100 text-slate-600 border-slate-300 ring-1 ring-slate-200/50',
          desc: 'Sample demo vacancy — verification not applicable',
        };
      case 'needs_verification':
      default:
        return {
          icon: '⚠️',
          label: 'Needs Verification',
          classes: 'bg-amber-50 text-amber-800 border-amber-300 ring-1 ring-amber-200/50',
          desc: 'Incomplete or unconfirmed evidence — verify manually',
        };
    }
  };

  const config = getBadgeConfig(status);

  const sizeStyles = {
    sm: 'text-2xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3.5 py-1.5 gap-2',
  }[size] || 'text-xs px-2.5 py-1 gap-1.5';

  return (
    <span
      className={`inline-flex items-center rounded-md border font-medium ${sizeStyles} ${config.classes} ${className}`}
      title={config.desc}
    >
      <span role="img" aria-label={config.label} className="select-none">
        {config.icon}
      </span>
      <span className="tracking-tight">{config.label}</span>
    </span>
  );
}
