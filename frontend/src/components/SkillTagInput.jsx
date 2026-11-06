import React, { useState } from 'react';

export const SkillTagInput = ({ category, label, tags = [], onTagsChange }) => {
  const [inputVal, setInputVal] = useState('');

  const addTag = (val) => {
    const trimmed = val.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onTagsChange([...tags, trimmed]);
    }
    setInputVal('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(inputVal);
    } else if (e.key === 'Backspace' && !inputVal && tags.length > 0) {
      onTagsChange(tags.slice(0, -1));
    }
  };

  const removeTag = (indexToRemove) => {
    onTagsChange(tags.filter((_, idx) => idx !== indexToRemove));
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-700">
          {label}
        </label>
        <span className="text-xs text-slate-400">
          {tags.length} added
        </span>
      </div>

      <div className="p-2.5 bg-white border border-slate-300 rounded-lg focus-within:ring-2 focus-within:ring-indigo-100 focus-within:border-indigo-600 transition-colors flex flex-wrap gap-2 items-center min-h-[46px]">
        {tags.map((tag, idx) => (
          <span
            key={idx}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(idx)}
              className="text-indigo-400 hover:text-indigo-700 font-bold focus:outline-none"
              aria-label={`Remove ${tag}`}
            >
              ×
            </button>
          </span>
        ))}

        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => {
            if (inputVal.trim()) addTag(inputVal);
          }}
          placeholder={tags.length === 0 ? "Type and press Enter or comma..." : "Add more..."}
          className="flex-1 min-w-[120px] bg-transparent text-sm text-slate-900 focus:outline-none py-0.5"
        />
      </div>
    </div>
  );
};

export default SkillTagInput;

