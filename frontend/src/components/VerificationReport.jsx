import React, { useState } from 'react';
import VerificationBadge from './VerificationBadge';
import { verificationAPI } from '../services/api';

export default function VerificationReport({
  jobId,
  verification,
  onVerificationUpdate,
  isSample = false,
}) {
  const [loading, setLoading] = useState(false);
  const [recruiterFormOpen, setRecruiterFormOpen] = useState(false);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('company'); // 'company' | 'recruiter' | 'job'

  // Recruiter form state
  const [recName, setRecName] = useState('');
  const [recEmail, setRecEmail] = useState('');
  const [recCompany, setRecCompany] = useState('');
  const [recSubmitting, setRecSubmitting] = useState(false);
  const [recError, setRecError] = useState('');

  // Report modal state
  const [reportReason, setReportReason] = useState('fee_request');
  const [reportNote, setReportNote] = useState('');
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [reportSuccess, setReportSuccess] = useState(false);
  const [reportError, setReportError] = useState('');

  const handleRunVerification = async () => {
    setLoading(true);
    try {
      const res = await verificationAPI.runVerification(jobId);
      if (res.data?.verification && onVerificationUpdate) {
        onVerificationUpdate(res.data.verification);
      }
    } catch (err) {
      console.error('Failed to run verification:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRecruiterSubmit = async (e) => {
    e.preventDefault();
    setRecError('');
    if (!recEmail || !recEmail.includes('@')) {
      setRecError('Please provide a valid recruiter email address.');
      return;
    }
    setRecSubmitting(true);
    try {
      const res = await verificationAPI.submitRecruiterDetails(jobId, {
        name: recName.trim() || undefined,
        email: recEmail.trim().toLowerCase(),
        claimed_company: recCompany.trim() || undefined,
      });
      if (res.data?.verification && onVerificationUpdate) {
        onVerificationUpdate(res.data.verification);
        setRecruiterFormOpen(false);
      }
    } catch (err) {
      setRecError(err.response?.data?.message || 'Failed to submit recruiter contact details.');
    } finally {
      setRecSubmitting(false);
    }
  };

  const handleReportSubmit = async (e) => {
    e.preventDefault();
    setReportError('');
    setReportSubmitting(true);
    try {
      await verificationAPI.reportJob(jobId, {
        reason: reportReason,
        note: reportNote.trim(),
      });
      setReportSuccess(true);
      setTimeout(() => {
        setReportModalOpen(false);
        setReportSuccess(false);
        setReportNote('');
      }, 2000);
    } catch (err) {
      setReportError(err.response?.data?.message || 'Failed to submit abuse report.');
    } finally {
      setReportSubmitting(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Never';
    try {
      return new Date(isoString).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'Recently';
    }
  };

  const company = verification?.company || { status: 'needs_verification', evidence: [], missing: [], warnings: [] };
  const recruiter = verification?.recruiter || { status: 'needs_verification', provided: false, contact: {}, evidence: [], missing: [], warnings: [] };
  const job = verification?.job || { status: 'needs_verification', evidence: [], missing: [], warnings: [] };
  const overallStatus = verification?.overall_status || 'needs_verification';
  const isSuspicious = overallStatus === 'suspicious';

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden space-y-6 p-6 sm:p-8">
      {/* 1. Mandatory Legal Disclaimer */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-3">
        <span className="text-base select-none">⚖️</span>
        <div className="space-y-0.5">
          <span className="font-semibold text-slate-800 block">Verification Evidence Notice</span>
          <p className="text-slate-600 leading-relaxed">
            This report shows available evidence. It is not a guarantee. Always do your own checks and never pay money to get a job.
          </p>
        </div>
      </div>

      {/* 2. Suspicious Critical Alert Banner if applicable */}
      {isSuspicious && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-300 text-xs text-rose-900 flex items-start gap-3 shadow-sm">
          <span className="text-2xl select-none">🚨</span>
          <div>
            <span className="font-bold uppercase tracking-wider text-rose-800 block">
              High-Risk Warning Indicators Detected
            </span>
            <p className="text-rose-700 mt-1 leading-relaxed">
              This posting exhibits indicators commonly associated with recruitment fraud (such as fee demands, sensitive credential requests, or unverified personal email channels). Do not share financial details, OTPs, or transfer any funds.
            </p>
          </div>
        </div>
      )}

      {/* 3. Overall Status & Recommended Action Card */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-xl p-5 sm:p-6 shadow-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-2xs font-semibold text-slate-300 uppercase tracking-wider">Overall Legitimacy Evaluation:</span>
              <VerificationBadge status={overallStatus} size="sm" />
            </div>
            <p className="text-sm text-slate-200 font-medium leading-relaxed max-w-2xl">
              {verification?.recommended_action || 'Run verification to evaluate available legitimacy evidence.'}
            </p>
            <div className="text-2xs text-slate-400 flex items-center gap-3 pt-1">
              <span>Last checked: {formatDate(verification?.checked_at)}</span>
              {verification?.checks_run?.length > 0 && (
                <span>• {verification.checks_run.length} checks executed</span>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleRunVerification}
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white rounded-lg text-xs font-semibold transition-all shadow-sm flex items-center gap-1.5"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <span>🛡️</span>
                  <span>{verification ? 'Re-check Verification' : 'Verify This Job'}</span>
                </>
              )}
            </button>

            <button
              onClick={() => setReportModalOpen(true)}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-rose-300 border border-slate-700 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1"
              title="Report suspicious vacancy"
            >
              <span>🚩</span>
              <span>Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4. Three-Entity Navigation Tabs */}
      <div>
        <div className="flex border-b border-slate-200 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('company')}
            className={`pb-3 px-4 border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'company'
                ? 'border-indigo-600 text-indigo-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>🏢 Company Legitimacy</span>
            <VerificationBadge status={company.status} size="sm" />
          </button>

          <button
            onClick={() => setActiveTab('recruiter')}
            className={`pb-3 px-4 border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'recruiter'
                ? 'border-indigo-600 text-indigo-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>👤 Recruiter Contact</span>
            <VerificationBadge status={recruiter.status} size="sm" />
          </button>

          <button
            onClick={() => setActiveTab('job')}
            className={`pb-3 px-4 border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'job'
                ? 'border-indigo-600 text-indigo-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>📄 Job Posting Integrity</span>
            <VerificationBadge status={job.status} size="sm" />
          </button>
        </div>
      </div>

      {/* 5. Tab Content: COMPANY */}
      {activeTab === 'company' && (
        <div className="space-y-5 animate-fadeIn">
          {/* Warnings if any */}
          {company.warnings?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-700">Warning Indicators</h4>
              <div className="space-y-2">
                {company.warnings.map((w, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2">
                    <span className="font-bold uppercase text-2xs px-1.5 py-0.5 rounded bg-rose-200 text-rose-900">
                      {w.severity}
                    </span>
                    <span>{w.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evidence found */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Evidence Found</h4>
            {company.evidence?.length > 0 ? (
              <div className="border border-slate-200 rounded-xl divide-y divide-slate-100 overflow-hidden text-xs">
                {company.evidence.map((ev, idx) => (
                  <div key={idx} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50 transition-colors">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-2xs font-bold px-2 py-0.5 rounded uppercase ${
                          ev.result === 'pass'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}>
                          {ev.result}
                        </span>
                        <span className="font-semibold text-slate-800 capitalize">
                          {ev.check.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-slate-600">{ev.detail}</p>
                    </div>

                    {ev.source_url && (
                      <a
                        href={ev.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-2xs font-semibold text-indigo-600 hover:text-indigo-800 underline self-start sm:self-center shrink-0"
                      >
                        Source Link ↗
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No direct verification evidence available yet.</p>
            )}
          </div>

          {/* Missing evidence */}
          {company.missing?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Unconfirmed / Missing Checks</h4>
              <ul className="list-disc list-inside text-xs text-slate-500 space-y-1 pl-1">
                {company.missing.map((m, idx) => (
                  <li key={idx}>{m}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Manual checks links */}
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-3 text-xs">
            <span className="font-semibold text-slate-700">Manual Verification:</span>
            <a
              href="https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do"
              target="_blank"
              rel="noopener noreferrer"
              className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium inline-flex items-center gap-1 transition-colors"
            >
              <span>🏛️ Check manually on MCA (India)</span>
              <span>↗</span>
            </a>
          </div>
        </div>
      )}

      {/* 6. Tab Content: RECRUITER */}
      {activeTab === 'recruiter' && (
        <div className="space-y-5 animate-fadeIn">
          {/* Recruiter contact summary */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-slate-400 block font-medium">Recruiter Contact Details:</span>
              {recruiter.provided && recruiter.contact?.email ? (
                <div className="mt-1 space-y-0.5">
                  <span className="font-bold text-slate-800 block text-sm">
                    {recruiter.contact.name || 'Unnamed Recruiter'}
                  </span>
                  <span className="text-indigo-600 font-mono">{recruiter.contact.email}</span>
                  {recruiter.contact.claimed_company && (
                    <span className="text-slate-500 block">Claimed: {recruiter.contact.claimed_company}</span>
                  )}
                </div>
              ) : (
                <p className="text-slate-500 mt-1 italic">No recruiter contact details provided for this posting.</p>
              )}
            </div>

            <button
              onClick={() => setRecruiterFormOpen(!recruiterFormOpen)}
              className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg font-semibold transition-colors text-xs shrink-0"
            >
              {recruiterFormOpen ? 'Close Form' : 'I received a message from a recruiter →'}
            </button>
          </div>

          {/* Interactive Recruiter Entry Form */}
          {recruiterFormOpen && (
            <form onSubmit={handleRecruiterSubmit} className="p-5 rounded-xl border border-indigo-200 bg-indigo-50/50 space-y-4">
              <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider">
                Verify Recruiter Message Or Direct Outreach
              </h4>
              <p className="text-xs text-indigo-700">
                If someone reached out to you claiming to represent this company, enter their details below to verify email domain legitimacy.
              </p>

              {recError && <p className="text-xs text-red-600 font-semibold">{recError}</p>}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-2xs font-semibold text-slate-600 mb-1">Recruiter Name</label>
                  <input
                    type="text"
                    value={recName}
                    onChange={(e) => setRecName(e.target.value)}
                    placeholder="e.g. John Doe"
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-2xs font-semibold text-slate-600 mb-1">Recruiter Email *</label>
                  <input
                    type="email"
                    required
                    value={recEmail}
                    onChange={(e) => setRecEmail(e.target.value)}
                    placeholder="e.g. recruiter@company.com"
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-2xs font-semibold text-slate-600 mb-1">Claimed Company</label>
                  <input
                    type="text"
                    value={recCompany}
                    onChange={(e) => setRecCompany(e.target.value)}
                    placeholder="e.g. Acme Corp"
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setRecruiterFormOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={recSubmitting}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg text-xs transition-colors shadow-sm disabled:opacity-50"
                >
                  {recSubmitting ? 'Evaluating...' : 'Verify Recruiter'}
                </button>
              </div>
            </form>
          )}

          {/* Recruiter warnings */}
          {recruiter.warnings?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-700">Warning Indicators</h4>
              <div className="space-y-2">
                {recruiter.warnings.map((w, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2">
                    <span className="font-bold uppercase text-2xs px-1.5 py-0.5 rounded bg-rose-200 text-rose-900">
                      {w.severity}
                    </span>
                    <span>{w.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recruiter evidence */}
          {recruiter.evidence?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Evidence Found</h4>
              <div className="border border-slate-200 rounded-xl divide-y divide-slate-100 overflow-hidden text-xs">
                {recruiter.evidence.map((ev, idx) => (
                  <div key={idx} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50 transition-colors">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-2xs font-bold px-2 py-0.5 rounded uppercase ${
                          ev.result === 'pass'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}>
                          {ev.result}
                        </span>
                        <span className="font-semibold text-slate-800 capitalize">
                          {ev.check.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-slate-600">{ev.detail}</p>
                    </div>

                    {ev.source_url && (
                      <a
                        href={ev.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-2xs font-semibold text-indigo-600 hover:text-indigo-800 underline self-start sm:self-center shrink-0"
                      >
                        LinkedIn Search ↗
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 7. Tab Content: JOB POSTING */}
      {activeTab === 'job' && (
        <div className="space-y-5 animate-fadeIn">
          {/* Job warnings */}
          {job.warnings?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-700">Detected Posting Warnings</h4>
              <div className="space-y-2">
                {job.warnings.map((w, idx) => (
                  <div key={idx} className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold uppercase text-2xs px-1.5 py-0.5 rounded bg-rose-200 text-rose-900">
                        {w.severity}
                      </span>
                      <span className="font-semibold text-rose-900">{w.code}</span>
                    </div>
                    <p>{w.message}</p>
                    {w.exact_quote && (
                      <div className="mt-1 p-2 rounded bg-white/70 border border-rose-100 text-2xs text-rose-900 font-mono">
                        Quote: "{w.exact_quote}"
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Job evidence */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Posting Scans & Evidence</h4>
            {job.evidence?.length > 0 ? (
              <div className="border border-slate-200 rounded-xl divide-y divide-slate-100 overflow-hidden text-xs">
                {job.evidence.map((ev, idx) => (
                  <div key={idx} className="p-3.5 flex items-start gap-2 hover:bg-slate-50 transition-colors">
                    <span className="text-emerald-700 font-bold">✓</span>
                    <div>
                      <span className="font-semibold text-slate-800 capitalize block">
                        {ev.check.replace(/_/g, ' ')}
                      </span>
                      <p className="text-slate-600 mt-0.5">{ev.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No posting evidence items available.</p>
            )}
          </div>
        </div>
      )}

      {/* 8. Report Modal Popup */}
      {reportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 animate-scaleUp">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span>🚩</span>
                <span>Report Suspicious Job Posting</span>
              </h3>
              <button
                onClick={() => setReportModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                &times;
              </button>
            </div>

            {reportSuccess ? (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold text-center">
                ✓ Report submitted successfully. Thank you for keeping freshers safe!
              </div>
            ) : (
              <form onSubmit={handleReportSubmit} className="space-y-4 text-xs">
                {reportError && <p className="text-red-600 font-semibold">{reportError}</p>}

                <div>
                  <label className="block text-2xs font-semibold text-slate-700 mb-1">Reason for Report *</label>
                  <select
                    value={reportReason}
                    onChange={(e) => setReportReason(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                  >
                    <option value="fee_request">Requested upfront fee or payment</option>
                    <option value="identity_theft">Requested sensitive credentials / OTP / Aadhaar upfront</option>
                    <option value="unofficial_channel">Asked to apply/chat via Telegram or WhatsApp only</option>
                    <option value="fake_company">Impersonating real company / fake business</option>
                    <option value="other">Other suspicious pattern</option>
                  </select>
                </div>

                <div>
                  <label className="block text-2xs font-semibold text-slate-700 mb-1">Additional Notes / Evidence</label>
                  <textarea
                    rows={3}
                    value={reportNote}
                    onChange={(e) => setReportNote(e.target.value)}
                    placeholder="Provide details about what happened or copy quotes from the communication..."
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setReportModalOpen(false)}
                    className="px-3 py-2 text-slate-600 hover:text-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={reportSubmitting}
                    className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-lg shadow-sm disabled:opacity-50"
                  >
                    {reportSubmitting ? 'Submitting...' : 'Submit Report'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
