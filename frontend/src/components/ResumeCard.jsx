import React, { useState } from 'react';
import { resumeAPI } from '../services/api';

export default function ResumeCard({
  resume,
  onPreview,
  onEdit,
  onDuplicate,
  onDelete,
}) {
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async (format) => {
    setDownloading(true);
    try {
      const response = await resumeAPI.downloadResume(resume.id, format);
      // Create a blob URL and trigger download
      const blob = new Blob([response.data], {
        type:
          format === 'pdf'
            ? 'application/pdf'
            : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        `${(resume.target_role || 'Resume').replace(/\s+/g, '_')}_v${
          resume.version || 1
        }.${format}`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Failed to download ${format.toUpperCase()}: ${err.message || 'Error'}`);
    } finally {
      setDownloading(false);
    }
  };

  // Extract skills preview
  const allSkills = [];
  (resume.content?.skills || []).forEach((cat) => {
    (cat.items || []).forEach((item) => {
      if (!allSkills.includes(item)) allSkills.push(item);
    });
  });

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-all p-5 flex flex-col justify-between">
      <div>
        {/* Top Badges & Role */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 block">
              {resume.target_role}
            </span>
            <h3 className="text-base font-bold text-slate-900 leading-snug">
              {resume.resume_name || `${resume.target_role} - v${resume.version}`}
            </h3>
          </div>
          <div className="flex flex-wrap items-center gap-1.5 justify-end">
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
              v{resume.version}
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 capitalize">
              {resume.template || 'modern'}
            </span>
            {resume.edited_by_user && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                Customized
              </span>
            )}
          </div>
        </div>

        {/* Outdated Warning Badge */}
        {resume.is_outdated && (
          <div className="my-2.5 p-2 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-1.5 text-xs text-amber-800">
            <span>⚠️</span>
            <span>
              <strong>Outdated:</strong> Master profile updated since generation.
            </span>
          </div>
        )}

        {/* Summary Snippet */}
        {resume.content?.summary && (
          <p className="text-xs text-slate-600 line-clamp-2 my-2 leading-relaxed">
            {resume.content.summary}
          </p>
        )}

        {/* Skills Snippet */}
        {allSkills.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {allSkills.slice(0, 6).map((skill, idx) => (
              <span
                key={idx}
                className="text-2xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium"
              >
                {skill}
              </span>
            ))}
            {allSkills.length > 6 && (
              <span className="text-2xs px-1.5 py-0.5 text-slate-400 font-medium">
                +{allSkills.length - 6} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-5 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onPreview(resume)}
            className="px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            👁️ Preview
          </button>
          <button
            onClick={() => onEdit(resume)}
            className="px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
          >
            ✏️ Edit
          </button>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => handleDownload('pdf')}
            disabled={downloading}
            className="px-2.5 py-1.5 text-xs font-semibold text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50"
            title="Download ATS PDF"
          >
            PDF
          </button>
          <button
            onClick={() => handleDownload('docx')}
            disabled={downloading}
            className="px-2.5 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50"
            title="Download ATS Word DOCX"
          >
            DOCX
          </button>
          <button
            onClick={() => onDuplicate(resume.id)}
            className="p-1.5 text-slate-400 hover:text-slate-700 text-xs rounded hover:bg-slate-100"
            title="Duplicate to new version"
          >
            📋
          </button>
          <button
            onClick={() => onDelete(resume.id, resume.target_role, resume.version)}
            className="p-1.5 text-slate-400 hover:text-red-600 text-xs rounded hover:bg-slate-100"
            title="Delete this resume"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>
  );
}

