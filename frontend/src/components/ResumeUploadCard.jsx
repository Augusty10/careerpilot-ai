import React, { useState, useRef } from 'react';
import { profileAPI } from '../services/api';
import Alert from './Alert';
import Button from './Button';

export const ResumeUploadCard = ({ onExtractionSuccess, isExtracted, onDismissBanner }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFileName, setSelectedFileName] = useState('');
  const fileInputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;

    setError('');
    setSelectedFileName(file.name);

    // Client-side extension validation
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (ext !== '.pdf' && ext !== '.docx') {
      setError('Unsupported file type. Please upload a PDF (.pdf) or Word document (.docx).');
      return;
    }

    // Client-side size validation (5 MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('File exceeds maximum size of 5 MB. Please upload a smaller document.');
      return;
    }

    const formData = new FormData();
    formData.append('resume', file);

    setUploading(true);

    try {
      const response = await profileAPI.uploadResume(formData);
      if (response.data && response.data.extracted_data) {
        onExtractionSuccess(response.data.extracted_data);
      }
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to parse resume document. Please verify your file or enter details manually.';
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <div className="space-y-4">
      {/* Upload Box Card */}
      <div className="bg-gradient-to-br from-indigo-50/80 via-white to-slate-50 p-6 rounded-2xl border border-indigo-100 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold mb-1.5">
              <span>AI Assisted</span>
              <span>•</span>
              <span>Fast Track</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900">
              Upload Existing Resume to Auto-Fill
            </h2>
            <p className="text-xs text-slate-600 mt-0.5">
              Save time! Let AI parse your PDF or Word document into your master profile.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-medium px-2 py-1 rounded bg-slate-100 text-slate-600 border border-slate-200">
              PDF / DOCX (Max 5MB)
            </span>
          </div>
        </div>

        {error && (
          <Alert type="error" message={error} className="mb-4" onClose={() => setError('')} />
        )}

        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-xl p-6 sm:p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-indigo-600 bg-indigo-50/50 scale-[0.99]'
              : 'border-slate-300 hover:border-indigo-400 hover:bg-indigo-50/30'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFile(e.target.files[0]);
              }
            }}
          />

          <div className="flex flex-col items-center justify-center gap-2">
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
                <div className="text-sm font-semibold text-slate-700">
                  Parsing {selectedFileName} with AI...
                </div>
                <p className="text-xs text-slate-500">
                  Extracting education, skills, projects, and work experience without hallucinations.
                </p>
              </div>
            ) : (
              <>
                <div className="w-12 h-12 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center mb-1">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-slate-800">
                  <span className="text-indigo-600 underline">Click to upload</span> or drag and drop your resume
                </p>
                <p className="text-xs text-slate-500">
                  Supports digital PDF and Word (.docx) documents up to 5 MB
                </p>
              </>
            )}
          </div>
        </div>

        {/* Privacy Note */}
        <div className="mt-3 flex items-start gap-2 text-[11px] text-slate-500">
          <svg className="w-4 h-4 shrink-0 text-slate-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span>
            <strong>Privacy Guarantee:</strong> Uploaded resumes are stored in private, isolated storage and processed via AI strictly for candidate data extraction. Your document is never shared publicly or used to train public models.
          </span>
        </div>
      </div>

      {/* Prominent Banner when AI extracted data is loaded */}
      {isExtracted && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 flex items-start justify-between gap-3 shadow-sm animate-pulse-once">
          <div className="flex items-start gap-3">
            <span className="text-xl">✨</span>
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-amber-950">
                AI extracted this information. Please review and correct it before saving.
              </h4>
              <p className="text-xs text-amber-800 leading-relaxed">
                We've auto-populated your education, skills, projects, and experiences based on your resume text. Any fields left empty or missing in the document are highlighted below so you can fill them in.
              </p>
            </div>
          </div>
          {onDismissBanner && (
            <button
              onClick={onDismissBanner}
              className="text-amber-700 hover:text-amber-950 text-sm font-semibold p-1"
              aria-label="Dismiss banner"
            >
              ✕
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ResumeUploadCard;

