import React, { useState } from 'react';
import { resumeAPI } from '../services/api';

export default function ResumeEditor({ resume, onSaveSuccess, onCancel }) {
  const [formData, setFormData] = useState(() => {
    // Deep clone content to prevent mutating parent state directly
    return {
      resume_name: resume.resume_name || '',
      template: resume.template || 'modern',
      content: JSON.parse(JSON.stringify(resume.content || {})),
    };
  });

  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [warnings, setWarnings] = useState([]);

  // Handle template change
  const handleTemplateChange = (tmpl) => {
    setFormData((prev) => ({ ...prev, template: tmpl }));
  };

  // Handle summary change
  const handleSummaryChange = (e) => {
    const val = e.target.value;
    setFormData((prev) => ({
      ...prev,
      content: { ...prev.content, summary: val },
    }));
  };

  // Handle project bullet point change
  const handleBulletChange = (projIdx, bulletIdx, value) => {
    setFormData((prev) => {
      const projects = [...(prev.content.projects || [])];
      const targetProj = { ...projects[projIdx] };
      const bullets = [...(targetProj.description_bullets || [])];
      bullets[bulletIdx] = value;
      targetProj.description_bullets = bullets;
      projects[projIdx] = targetProj;
      return {
        ...prev,
        content: { ...prev.content, projects },
      };
    });
  };

  const handleAddBullet = (projIdx) => {
    setFormData((prev) => {
      const projects = [...(prev.content.projects || [])];
      const targetProj = { ...projects[projIdx] };
      const bullets = [...(targetProj.description_bullets || []), 'New bullet point...'];
      targetProj.description_bullets = bullets;
      projects[projIdx] = targetProj;
      return {
        ...prev,
        content: { ...prev.content, projects },
      };
    });
  };

  const handleRemoveBullet = (projIdx, bulletIdx) => {
    setFormData((prev) => {
      const projects = [...(prev.content.projects || [])];
      const targetProj = { ...projects[projIdx] };
      const bullets = (targetProj.description_bullets || []).filter((_, idx) => idx !== bulletIdx);
      targetProj.description_bullets = bullets;
      projects[projIdx] = targetProj;
      return {
        ...prev,
        content: { ...prev.content, projects },
      };
    });
  };

  // Handle category skill removal or add
  const handleRemoveSkill = (catIdx, skillIdx) => {
    setFormData((prev) => {
      const skills = [...(prev.content.skills || [])];
      const targetCat = { ...skills[catIdx] };
      targetCat.items = (targetCat.items || []).filter((_, idx) => idx !== skillIdx);
      skills[catIdx] = targetCat;
      return {
        ...prev,
        content: { ...prev.content, skills },
      };
    });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg('');
    setWarnings([]);

    try {
      const res = await resumeAPI.updateResume(resume.id, formData);
      if (res.data.status === 'success') {
        if (res.data.warnings && res.data.warnings.length > 0) {
          setWarnings(res.data.warnings);
        }
        if (onSaveSuccess) {
          onSaveSuccess(res.data.resume, res.data.warnings);
        }
      }
    } catch (err) {
      const msg = err.response?.data?.message || 'Failed to save resume edits.';
      setErrorMsg(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
      <div className="bg-slate-900 px-6 py-4 flex items-center justify-between text-white">
        <div>
          <h2 className="text-lg font-bold">Edit Resume: {resume.target_role}</h2>
          <p className="text-xs text-slate-400">
            Version {resume.version} • Customise presentation and impact bullets
          </p>
        </div>
        <button
          onClick={onCancel}
          className="text-slate-400 hover:text-white text-sm px-2 py-1"
        >
          ✕ Close
        </button>
      </div>

      <form onSubmit={handleSave} className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
        {errorMsg && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {errorMsg}
          </div>
        )}

        {warnings.length > 0 && (
          <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-sm space-y-1">
            <p className="font-semibold">Truthfulness Verification Alerts:</p>
            <ul className="list-disc list-inside text-xs space-y-0.5">
              {warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Basic Settings */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Resume Name
            </label>
            <input
              type="text"
              value={formData.resume_name}
              onChange={(e) => setFormData({ ...formData, resume_name: e.target.value })}
              className="w-full text-sm rounded-md border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              placeholder="e.g. Python Developer - Backend Focus"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Visual ATS Template
            </label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => handleTemplateChange('modern')}
                className={`flex-1 text-xs py-2 px-3 rounded-md font-semibold border transition-all ${
                  formData.template === 'modern'
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                }`}
              >
                Modern (Clean Sans-Serif)
              </button>
              <button
                type="button"
                onClick={() => handleTemplateChange('classic')}
                className={`flex-1 text-xs py-2 px-3 rounded-md font-semibold border transition-all ${
                  formData.template === 'classic'
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                }`}
              >
                Classic (Traditional Serif)
              </button>
            </div>
          </div>
        </div>

        {/* Truthfulness Notice */}
        <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-xs text-indigo-900 flex items-start gap-2">
          <span className="text-base leading-none">🛡️</span>
          <div>
            <span className="font-bold">CareerPilot AI Truthfulness Guarantee:</span> Personal
            details and education are synced directly with your verified Master Profile. Skills
            are checked against your master profile to eliminate ATS hallucinations.
          </div>
        </div>

        {/* Professional Summary */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-xs font-semibold text-slate-700">
              Professional Summary
            </label>
            <span className="text-xs text-slate-400">
              {formData.content?.summary?.length || 0} / 1000 characters
            </span>
          </div>
          <textarea
            rows={4}
            value={formData.content?.summary || ''}
            onChange={handleSummaryChange}
            maxLength={1000}
            className="w-full text-sm rounded-md border border-slate-300 p-3 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            placeholder="Write a targeted 2-3 sentence summary tailored for this specific role..."
          />
        </div>

        {/* Skills Management */}
        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1">
            Technical Skills (Role Grouping)
          </label>
          <div className="space-y-3 bg-slate-50 p-4 rounded-lg border border-slate-200">
            {formData.content?.skills?.map((cat, catIdx) => (
              <div key={catIdx} className="bg-white p-3 rounded border border-slate-200">
                <span className="font-semibold text-xs text-slate-900 block mb-2">
                  {cat.category}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {cat.items?.map((item, itemIdx) => (
                    <span
                      key={itemIdx}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-slate-100 text-slate-700 border border-slate-200"
                    >
                      {item}
                      <button
                        type="button"
                        onClick={() => handleRemoveSkill(catIdx, itemIdx)}
                        className="text-slate-400 hover:text-red-500 font-bold ml-1"
                        title="Remove from this resume"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  {(!cat.items || cat.items.length === 0) && (
                    <span className="text-xs text-slate-400 italic">No skills in this category</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Project Bullets */}
        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1">
            Key Projects & Accomplishment Bullets
          </label>
          <div className="space-y-4">
            {formData.content?.projects?.map((proj, pIdx) => (
              <div key={pIdx} className="border border-slate-200 rounded-lg p-4 bg-slate-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm text-slate-900">{proj.title}</span>
                  {proj.tech_stack && (
                    <span className="text-xs text-indigo-600 font-medium">
                      [{proj.tech_stack.join(', ')}]
                    </span>
                  )}
                </div>
                <div className="space-y-2">
                  {proj.description_bullets?.map((bullet, bIdx) => (
                    <div key={bIdx} className="flex items-start gap-2">
                      <span className="text-slate-400 text-xs mt-2">•</span>
                      <textarea
                        rows={2}
                        value={bullet}
                        onChange={(e) => handleBulletChange(pIdx, bIdx, e.target.value)}
                        className="flex-1 text-xs rounded border border-slate-300 p-2 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveBullet(pIdx, bIdx)}
                        className="text-slate-400 hover:text-red-500 p-1 text-sm"
                        title="Delete bullet"
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => handleAddBullet(pIdx)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold mt-1 inline-block"
                  >
                    + Add Bullet Point
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
          <button
            type="button"
            onClick={onCancel}
            disabled={saving}
            className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Saving & Re-exporting...
              </>
            ) : (
              'Save & Update Resume'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

