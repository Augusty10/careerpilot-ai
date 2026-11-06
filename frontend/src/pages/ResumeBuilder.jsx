import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { resumeAPI, profileAPI } from '../services/api';
import ResumeCard from '../components/ResumeCard';
import ResumePreview from '../components/ResumePreview';
import ResumeEditor from '../components/ResumeEditor';

export default function ResumeBuilder() {
  const [resumes, setResumes] = useState([]);
  const [predefinedRoles, setPredefinedRoles] = useState([]);
  const [masterProfileStatus, setMasterProfileStatus] = useState('draft');
  const [loading, setLoading] = useState(true);

  // Generation state
  const [selectedRole, setSelectedRole] = useState('Full Stack Developer');
  const [customRole, setCustomRole] = useState('');
  const [template, setTemplate] = useState('modern');
  const [batchMode, setBatchMode] = useState(false);
  const [selectedBatchRoles, setSelectedBatchRoles] = useState(['Python Developer', 'Full Stack Developer']);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState('');
  const [genSuccess, setGenSuccess] = useState('');
  const [genWarnings, setGenWarnings] = useState([]);

  // Filter state
  const [roleFilter, setRoleFilter] = useState('all');

  // Modal state
  const [activeResumeForPreview, setActiveResumeForPreview] = useState(null);
  const [activeResumeForEdit, setActiveResumeForEdit] = useState(null);
  const [previewTemplate, setPreviewTemplate] = useState('modern');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [resumesRes, rolesRes] = await Promise.all([
        resumeAPI.listResumes(),
        resumeAPI.getRoles().catch(() => ({ data: { roles: [] } })),
      ]);

      setResumes(resumesRes.data.resumes || []);
      setMasterProfileStatus(resumesRes.data.master_profile_status || 'draft');

      if (rolesRes.data?.roles?.length > 0) {
        setPredefinedRoles(rolesRes.data.roles);
        if (!selectedRole && rolesRes.data.roles[0]) {
          setSelectedRole(rolesRes.data.roles[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load resumes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setGenError('');
    setGenSuccess('');
    setGenWarnings([]);

    try {
      if (batchMode) {
        if (!selectedBatchRoles || selectedBatchRoles.length === 0) {
          throw new Error('Please select at least one role for batch generation.');
        }
        const res = await resumeAPI.generateMultipleResumes({
          target_roles: selectedBatchRoles,
          template,
        });
        setGenSuccess(`Successfully generated ${res.data.resumes.length} role-specific resumes!`);
        await loadData();
      } else {
        const targetRoleToUse = customRole.trim() || selectedRole;
        if (!targetRoleToUse) {
          throw new Error('Please select or enter a target role.');
        }
        const res = await resumeAPI.generateResume({
          target_role: targetRoleToUse,
          template,
        });
        setGenSuccess(`Generated tailored resume for ${res.data.resume.target_role} (v${res.data.resume.version})!`);
        if (res.data.warnings && res.data.warnings.length > 0) {
          setGenWarnings(res.data.warnings);
        }
        await loadData();
      }
    } catch (err) {
      setGenError(err.response?.data?.message || err.message || 'Generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDuplicate = async (id) => {
    try {
      await resumeAPI.duplicateResume(id);
      await loadData();
    } catch (err) {
      alert(`Duplicate failed: ${err.response?.data?.message || err.message}`);
    }
  };

  const handleDelete = async (id, role, version) => {
    if (!window.confirm(`Are you sure you want to delete "${role} (v${version})"?`)) {
      return;
    }
    try {
      await resumeAPI.deleteResume(id);
      await loadData();
    } catch (err) {
      alert(`Delete failed: ${err.response?.data?.message || err.message}`);
    }
  };

  const handlePreviewOpen = (resume) => {
    setActiveResumeForPreview(resume);
    setPreviewTemplate(resume.template || 'modern');
  };

  const handleEditOpen = (resume) => {
    setActiveResumeForEdit(resume);
  };

  const handleEditSaveSuccess = (updatedResume) => {
    setActiveResumeForEdit(null);
    loadData();
  };

  const toggleBatchRole = (role) => {
    setSelectedBatchRoles((prev) => {
      if (prev.includes(role)) {
        return prev.filter((r) => r !== role);
      } else {
        if (prev.length >= 5) {
          alert('Maximum 5 roles can be generated in one batch.');
          return prev;
        }
        return [...prev, role];
      }
    });
  };

  // Filtered resumes
  const filteredResumes =
    roleFilter === 'all'
      ? resumes
      : resumes.filter((r) => r.target_role === roleFilter);

  // Unique target roles in user's library
  const availableRolesInLibrary = Array.from(new Set(resumes.map((r) => r.target_role)));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Multiple Resume Generator
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            One Profile. Multiple Careers. Generate truthful, role-targeted ATS resumes tailored for freshers.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-3">
          <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 text-center">
            <span className="text-xl font-bold text-indigo-600 block leading-none">
              {resumes.length}
            </span>
            <span className="text-3xs uppercase tracking-wider text-slate-500 font-semibold">
              Resumes
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 text-center">
            <span className="text-xl font-bold text-slate-800 block leading-none">
              {availableRolesInLibrary.length}
            </span>
            <span className="text-3xs uppercase tracking-wider text-slate-500 font-semibold">
              Roles
            </span>
          </div>
        </div>
      </div>

      {/* Unapproved Master Profile Warning */}
      {masterProfileStatus !== 'approved' && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <span className="text-xl">⚠️</span>
              <div>
                <h3 className="text-sm font-bold text-amber-800">
                  Master Profile Approval Required
                </h3>
                <p className="text-xs text-amber-700 mt-1">
                  To ensure 100% truthfulness and eliminate ATS hallucinations, your Master Career Profile
                  must be reviewed and marked as "Approved" before you can generate role-specific resumes.
                </p>
              </div>
            </div>
            <Link
              to="/profile"
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs rounded-lg shadow-sm whitespace-nowrap transition-colors"
            >
              Approve Master Profile →
            </Link>
          </div>
        </div>
      )}

      {/* Generation Hub */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Generate Role-Specific Resumes
            </h2>
            <p className="text-xs text-slate-500">
              AI selects relevant projects, prioritizes role competencies, and tailors summary & bullets.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setBatchMode(!batchMode)}
              className={`text-xs px-3 py-1.5 rounded-lg font-semibold border transition-all ${
                batchMode
                  ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
                  : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {batchMode ? '✓ Batch Mode (Multi-Role)' : '+ Multi-Role Batch'}
            </button>
          </div>
        </div>

        {/* Generation Feedback Alerts */}
        {genError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {genError}
          </div>
        )}
        {genSuccess && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-800 rounded-lg text-sm">
            {genSuccess}
          </div>
        )}
        {genWarnings.length > 0 && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-xs space-y-1">
            <span className="font-bold">Truthfulness Validation Note:</span>
            <ul className="list-disc list-inside">
              {genWarnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        <form onSubmit={handleGenerate} className="space-y-6">
          {!batchMode ? (
            /* Single Role Mode */
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-2">
                  Select Target Career Role
                </label>
                <div className="flex flex-wrap gap-2">
                  {predefinedRoles.map((role) => (
                    <button
                      key={role}
                      type="button"
                      onClick={() => {
                        setSelectedRole(role);
                        setCustomRole('');
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                        selectedRole === role && !customRole
                          ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {role}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Or Enter a Custom Role Title
                </label>
                <input
                  type="text"
                  value={customRole}
                  onChange={(e) => setCustomRole(e.target.value)}
                  placeholder="e.g. Cloud Security Specialist, DevOps Engineer, Mobile iOS Developer"
                  className="w-full text-sm rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
            </div>
          ) : (
            /* Multi-Role Batch Mode */
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-700">
                  Select Up to 5 Roles for Batch Generation:
                </label>
                <span className="text-xs text-indigo-600 font-bold">
                  {selectedBatchRoles.length} / 5 selected
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {predefinedRoles.map((role) => {
                  const isChecked = selectedBatchRoles.includes(role);
                  return (
                    <button
                      key={role}
                      type="button"
                      onClick={() => toggleBatchRole(role)}
                      className={`text-left px-3 py-2 rounded-lg text-xs font-medium border transition-all flex items-center justify-between ${
                        isChecked
                          ? 'bg-indigo-50 border-indigo-300 text-indigo-800'
                          : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      <span>{role}</span>
                      <span>{isChecked ? '✓' : '+'}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Template Selection */}
          <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-xs font-semibold text-slate-700">ATS Template:</span>
              <label className="inline-flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="template"
                  value="modern"
                  checked={template === 'modern'}
                  onChange={() => setTemplate('modern')}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                <span>Modern (Sans-Serif)</span>
              </label>
              <label className="inline-flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="template"
                  value="classic"
                  checked={template === 'classic'}
                  onChange={() => setTemplate('classic')}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                <span>Classic (Serif)</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={generating || masterProfileStatus !== 'approved'}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-semibold text-xs rounded-xl shadow-sm transition-all flex items-center justify-center gap-2"
            >
              {generating ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span>Generating Tailored Resume(s)...</span>
                </>
              ) : (
                <span>
                  {batchMode
                    ? `Generate ${selectedBatchRoles.length} Resumes Now`
                    : `Generate ${customRole.trim() || selectedRole} Resume`}
                </span>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Resumes Library */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Your Resume Library</h2>
            <p className="text-xs text-slate-500">
              Multiple role variants ready to download, tailor, or duplicate.
            </p>
          </div>

          {/* Role Filter Tabs */}
          {availableRolesInLibrary.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5">
              <button
                onClick={() => setRoleFilter('all')}
                className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors ${
                  roleFilter === 'all'
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                All Roles ({resumes.length})
              </button>
              {availableRolesInLibrary.map((role) => {
                const count = resumes.filter((r) => r.target_role === role).length;
                return (
                  <button
                    key={role}
                    onClick={() => setRoleFilter(role)}
                    className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors ${
                      roleFilter === role
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {role} ({count})
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Resumes Grid */}
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading your resumes...</div>
        ) : filteredResumes.length === 0 ? (
          <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center space-y-3">
            <span className="text-4xl block">📄</span>
            <h3 className="text-base font-bold text-slate-800">No resumes generated yet</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Select one or more target roles above to create your first role-tailored resumes directly
              from your master career profile.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredResumes.map((resume) => (
              <ResumeCard
                key={resume.id}
                resume={resume}
                onPreview={handlePreviewOpen}
                onEdit={handleEditOpen}
                onDuplicate={handleDuplicate}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {activeResumeForPreview && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="bg-slate-900 px-6 py-4 flex items-center justify-between text-white">
              <div>
                <h3 className="text-base font-bold">
                  {activeResumeForPreview.resume_name || activeResumeForPreview.target_role}
                </h3>
                <p className="text-xs text-slate-400">
                  Version {activeResumeForPreview.version} • ATS Single-Column Layout
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex bg-slate-800 rounded-lg p-0.5 border border-slate-700 text-xs">
                  <button
                    onClick={() => setPreviewTemplate('modern')}
                    className={`px-3 py-1 rounded-md font-medium transition-colors ${
                      previewTemplate === 'modern'
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Modern
                  </button>
                  <button
                    onClick={() => setPreviewTemplate('classic')}
                    className={`px-3 py-1 rounded-md font-medium transition-colors ${
                      previewTemplate === 'classic'
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Classic
                  </button>
                </div>

                <button
                  onClick={() => setActiveResumeForPreview(null)}
                  className="text-slate-400 hover:text-white text-base px-2 py-1"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto bg-slate-100 p-6">
              <ResumePreview
                resume={activeResumeForPreview}
                template={previewTemplate}
              />
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {activeResumeForEdit && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="max-w-3xl w-full">
            <ResumeEditor
              resume={activeResumeForEdit}
              onSaveSuccess={handleEditSaveSuccess}
              onCancel={() => setActiveResumeForEdit(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

