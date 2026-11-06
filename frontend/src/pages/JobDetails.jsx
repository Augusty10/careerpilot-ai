import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { jobAPI } from '../services/api';

export default function JobDetails() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadJobDetails();
  }, [jobId]);

  const loadJobDetails = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await jobAPI.getJob(jobId);
      if (res.data?.job) {
        setJob(res.data.job);
      } else {
        setErrorMsg('Job posting not found.');
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.message || 'Failed to load job details.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSave = async () => {
    if (!job || saving) return;
    setSaving(true);
    try {
      if (job.is_saved) {
        await jobAPI.unsaveJob(job.job_id);
        setJob((prev) => ({ ...prev, is_saved: false }));
      } else {
        await jobAPI.saveJob(job.job_id);
        setJob((prev) => ({ ...prev, is_saved: true }));
      }
    } catch (err) {
      alert(`Save action failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Not specified';
    try {
      return new Date(isoString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return 'Recently';
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-slate-500">
        Loading job vacancy details...
      </div>
    );
  }

  if (errorMsg || !job) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <p className="text-red-600 font-semibold">{errorMsg || 'Job not found.'}</p>
        <Link
          to="/jobs"
          className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold"
        >
          ← Back to Job Discovery
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate(-1)}
          className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1 transition-colors"
        >
          ← Back
        </button>
      </div>

      {/* Sample Listing Banner */}
      {job.is_sample && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-3 shadow-sm">
          <span className="text-xl">⚠️</span>
          <div>
            <span className="font-bold block uppercase tracking-wider text-amber-800">
              Sample listing — not a real vacancy
            </span>
            <p className="text-amber-700 mt-0.5">
              This is a curated demo vacancy for CareerPilot AI testing and demonstration. The application
              link leads to a sample placeholder.
            </p>
          </div>
        </div>
      )}

      {/* Header Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 block mb-1">
              {job.company}
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 leading-tight">
              {job.title}
            </h1>
            <div className="flex flex-wrap items-center gap-2 mt-3">
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium capitalize">
                📍 {job.location} ({job.work_mode})
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium capitalize">
                💼 {job.job_type.replace('_', ' ')}
              </span>
              <span
                className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                  job.fresher_status === 'fresher_friendly'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : job.fresher_status === 'entry_level'
                    ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                    : 'bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {job.fresher_status === 'fresher_friendly'
                  ? '🌱 Fresher Friendly'
                  : job.fresher_status === 'entry_level'
                  ? '⚡ Entry Level (0-2 Yrs)'
                  : job.fresher_status === 'experience_required'
                  ? '💼 Experience Required (>2 Yrs)'
                  : '❓ Unstated Experience'}
              </span>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              id="btn-save-job"
              onClick={handleToggleSave}
              disabled={saving}
              className={`px-4 py-2.5 rounded-xl border text-xs font-semibold transition-all flex items-center gap-1.5 ${
                job.is_saved
                  ? 'bg-rose-50 border-rose-200 text-rose-700 hover:bg-rose-100'
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <span>{job.is_saved ? '❤️' : '🤍'}</span>
              <span>{job.is_saved ? 'Saved' : 'Save Job'}</span>
            </button>

            <a
              href={job.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5"
            >
              <span>Open Original Posting</span>
              <span>↗</span>
            </a>
          </div>
        </div>
      </div>

      {/* Module 5 & 6 Placeholder */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 text-center">
        <div className="inline-flex items-center gap-2 text-indigo-700 font-semibold text-xs tracking-wide uppercase">
          <span>🎯</span>
          <span>Eligibility Match & Verification</span>
        </div>
        <p className="text-xs text-slate-500 mt-1 max-w-lg mx-auto">
          Candidate eligibility match scoring (Module 5) and recruiter verification (Module 6) coming soon.
        </p>
      </div>

      {/* Job Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Description */}
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-3">Job Description</h2>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
              {job.description}
            </p>
          </div>

          {/* Skills Required */}
          {job.required_skills && job.required_skills.length > 0 && (
            <div>
              <h2 className="text-base font-bold text-slate-900 mb-3">Required Technical Competencies</h2>
              <div className="flex flex-wrap gap-2">
                {job.required_skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-800 border border-indigo-100"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Overview & Requirements
            </h3>

            <div className="text-xs space-y-3">
              <div>
                <span className="text-slate-400 block font-medium">Experience Level</span>
                <span className="font-semibold text-slate-800">
                  {job.experience_text || 'Not specified'}
                </span>
              </div>

              {job.education_required && (
                <div>
                  <span className="text-slate-400 block font-medium">Education</span>
                  <span className="font-semibold text-slate-800">{job.education_required}</span>
                </div>
              )}

              {job.salary_text && (
                <div>
                  <span className="text-slate-400 block font-medium">Compensation</span>
                  <span className="font-bold text-emerald-700">{job.salary_text}</span>
                </div>
              )}

              <div>
                <span className="text-slate-400 block font-medium">Posted Date</span>
                <span className="font-semibold text-slate-800">{formatDate(job.posted_at)}</span>
              </div>

              {job.deadline && (
                <div>
                  <span className="text-slate-400 block font-medium">Application Deadline</span>
                  <span className="font-semibold text-slate-800">{formatDate(job.deadline)}</span>
                </div>
              )}

              <div>
                <span className="text-slate-400 block font-medium">Source</span>
                <span className="font-semibold text-slate-800 capitalize">{job.source}</span>
              </div>

              <div>
                <span className="text-slate-400 block font-medium">Last Verified</span>
                <span className="font-semibold text-slate-800">{formatDate(job.last_checked_at)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
