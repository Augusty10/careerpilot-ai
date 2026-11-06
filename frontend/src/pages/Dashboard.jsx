import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { profileAPI, resumeAPI, jobAPI, matchingAPI } from '../services/api';
import Button from '../components/Button';

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [resumeCount, setResumeCount] = useState(0);
  const [savedJobsCount, setSavedJobsCount] = useState(0);
  const [matchStats, setMatchStats] = useState({ strong_match: 0, partial_match: 0, low_match: 0, not_eligible: 0 });
  const [profileLoading, setProfileLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [profileRes, resumesRes, savedRes, recRes] = await Promise.all([
          profileAPI.getProfile().catch(() => ({ data: { profile: null } })),
          resumeAPI.listResumes().catch(() => ({ data: { resumes: [] } })),
          jobAPI.getSavedJobs().catch(() => ({ data: { saved_jobs: [] } })),
          matchingAPI.getRecommendedJobs({ limit: 1 }).catch(() => ({ data: { stats: null } })),
        ]);
        if (profileRes.data && profileRes.data.profile) {
          setProfile(profileRes.data.profile);
        }
        if (resumesRes.data && resumesRes.data.resumes) {
          setResumeCount(resumesRes.data.resumes.length);
        }
        if (savedRes.data && savedRes.data.saved_jobs) {
          setSavedJobsCount(savedRes.data.saved_jobs.length);
        }
        if (recRes.data?.stats) {
          setMatchStats(recRes.data.stats);
        }
      } catch (err) {
        // Fallback gracefully
      } finally {
        setProfileLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isApproved = profile?.profile_status === 'approved';

  const formatDate = (isoString) => {
    if (!isoString) return 'Recently';
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-indigo-700 via-indigo-600 to-indigo-800 rounded-3xl p-6 sm:p-10 text-white shadow-xl shadow-indigo-200/50 mb-8 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-white/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />

        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-sm text-xs font-semibold tracking-wide uppercase text-indigo-100 mb-4 border border-white/20">
            <span>Module 5 Active</span>
            <span>•</span>
            <span>AI Job Matching & Eligibility</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Welcome, {user?.name || 'Fresher'}! 👋
          </h1>

          <p className="mt-3 text-base sm:text-lg text-indigo-100 font-light leading-relaxed">
            One Profile. Multiple Careers. Smarter Applications.
          </p>

          <p className="mt-2 text-sm text-indigo-200">
            Compare your master profile against job criteria with transparent, explainable skill coverage and eligibility scoring.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/jobs/recommended">
              <Button variant="secondary" className="bg-white text-indigo-900 hover:bg-slate-100 shadow-sm border-0 font-semibold flex items-center gap-1.5">
                <span>🎯</span>
                <span>Recommended ({matchStats.strong_match} Strong)</span>
              </Button>
            </Link>
            <Link to="/jobs">
              <Button variant="outline" className="text-white border-white/30 hover:bg-white/10">
                Find Jobs (Saved: {savedJobsCount})
              </Button>
            </Link>
            <Link to="/resumes">
              <Button variant="outline" className="text-white border-white/30 hover:bg-white/10">
                Resumes ({resumeCount})
              </Button>
            </Link>
            <Link to="/profile">
              <Button variant="outline" className="text-white border-white/30 hover:bg-white/10">
                {isApproved ? 'Master Profile' : 'Complete Profile'}
              </Button>
            </Link>
            <Button
              variant="ghost"
              onClick={handleLogout}
              className="text-indigo-200 hover:text-white hover:bg-white/10"
            >
              Sign Out
            </Button>
          </div>
        </div>
      </div>

      {/* Profile Callout Prompt if Not Approved */}
      {!profileLoading && !isApproved && (
        <div className="mb-8 p-5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-lg shrink-0">
              ⚡
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Complete your Master Profile
              </h3>
              <p className="text-xs text-slate-600 mt-0.5">
                Upload your resume or fill in your details to create the single source of truth for all your upcoming AI applications.
              </p>
            </div>
          </div>
          <Link to="/profile">
            <Button variant="primary" size="sm" className="whitespace-nowrap shadow-sm">
              Complete Profile →
            </Button>
          </Link>
        </div>
      )}

      {/* Account Overview & Fresher Modules */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Snapshot Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              Candidate Snapshot
            </h2>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Name</span>
                <span className="text-slate-900 font-semibold">{user?.name}</span>
              </div>

              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Email</span>
                <span className="text-slate-900 font-semibold truncate max-w-[180px]">{user?.email}</span>
              </div>

              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Master Profile</span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                  isApproved
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {isApproved ? 'Approved ✅' : 'Draft / Incomplete'}
                </span>
              </div>

              <div className="flex justify-between py-2">
                <span className="text-slate-500 font-medium">Completeness</span>
                <span className="text-slate-900 font-bold">{profile?.completeness || 0}%</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-center">
            <Link to="/profile" className="text-xs font-semibold text-indigo-600 hover:underline">
              Manage Master Career Profile →
            </Link>
          </div>
        </div>

        {/* Modular Architecture Roadmap */}
        <div className="md:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-500" />
                CareerPilot AI Modules
              </h2>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
                Step 2 of 5
              </span>
            </div>

            <p className="text-sm text-slate-600 mb-4">
              Module 2 provides the structured foundation. All future resumes, job matching, and agent submissions are powered by this master profile.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-emerald-800">Module 1: User & Auth</span>
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">Active</span>
                </div>
                <p className="text-xs text-emerald-700 mt-1">JWT sessions, bcrypt security & password reset.</p>
              </div>

              <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-emerald-800">Module 2: Master Career Profile</span>
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">Active</span>
                </div>
                <p className="text-xs text-emerald-700 mt-1">PDF/DOCX AI extraction & verified profile truth.</p>
              </div>

              <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-emerald-800">Module 3: Multiple Resume Generator</span>
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">Active</span>
                </div>
                <p className="text-xs text-emerald-700 mt-1">Role-specific ATS resumes, truthfulness validator & exports.</p>
              </div>

              <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-emerald-800">Module 4: AI Job Discovery</span>
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">Active</span>
                </div>
                <p className="text-xs text-emerald-700 mt-1">Normalized fresher vacancies, dedup, and saved pipeline.</p>
              </div>

              <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-emerald-800">Module 5: Matching & Eligibility</span>
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">Active</span>
                </div>
                <p className="text-xs text-emerald-700 mt-1">Multi-criteria deterministic match, coverage scoring & gap analysis.</p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 opacity-70">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-slate-700">Module 6: Recruiter Verification</span>
                  <span className="text-[10px] font-medium text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">Upcoming</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Company legitimacy, ghost job detection & recruiter validation.</p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">Need to update your contact or password?</span>
            <Link to="/settings" className="text-xs font-semibold text-indigo-600 hover:underline">
              Go to Settings →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
