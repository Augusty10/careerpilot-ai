import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/Button';

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

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
            <span>Module 1 Active</span>
            <span>•</span>
            <span>Fresher Career Platform</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Welcome, {user?.name || 'Fresher'}! 👋
          </h1>

          <p className="mt-3 text-base sm:text-lg text-indigo-100 font-light leading-relaxed">
            One Profile. Multiple Careers. Smarter Applications.
          </p>

          <p className="mt-2 text-sm text-indigo-200">
            Your career portal is ready. Module 1 (Authentication & User Access) is active and verified.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/settings">
              <Button variant="secondary" className="bg-white text-indigo-900 hover:bg-slate-100 shadow-sm border-0 font-semibold">
                Account Settings
              </Button>
            </Link>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="text-white border-white/30 hover:bg-white/10"
            >
              Sign Out
            </Button>
          </div>
        </div>
      </div>

      {/* Account Overview & Fresher Modules */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Snapshot Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            Active Session Info
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
              <span className="text-slate-500 font-medium">Member Since</span>
              <span className="text-slate-900">{formatDate(user?.created_at)}</span>
            </div>

            <div className="flex justify-between py-2">
              <span className="text-slate-500 font-medium">Auth Status</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                Verified JWT
              </span>
            </div>
          </div>
        </div>

        {/* Modular Architecture Roadmap Placeholder */}
        <div className="md:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-500" />
                CareerPilot AI Modules
              </h2>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
                Step 1 of 5
              </span>
            </div>

            <p className="text-sm text-slate-600 mb-4">
              Authentication is complete! All subsequent modules will plug directly into the reusable <code className="px-1.5 py-0.5 bg-slate-100 rounded text-indigo-600 font-mono text-xs">@token_required</code> decorator and session context.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-emerald-800">Module 1: User & Auth</span>
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">Ready</span>
                </div>
                <p className="text-xs text-emerald-700 mt-1">JWT sessions, bcrypt security & password reset.</p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 opacity-70">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-slate-700">Module 2: Master Career Profile</span>
                  <span className="text-[10px] font-medium text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">Upcoming</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Education, projects, internships & skills.</p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 opacity-70">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-slate-700">Module 3: AI Resume Agent</span>
                  <span className="text-[10px] font-medium text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">Upcoming</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Multiple role-specific resume generation.</p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 opacity-70">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-slate-700">Module 4: Switch Agents</span>
                  <span className="text-[10px] font-medium text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">Upcoming</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Job discovery, verification & coordinator.</p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">Need to change your name or password?</span>
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

