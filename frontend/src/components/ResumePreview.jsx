import React from 'react';

export default function ResumePreview({ resume, template = 'modern' }) {
  if (!resume || !resume.content) {
    return (
      <div className="p-8 text-center text-slate-500 bg-slate-50 rounded-lg border border-slate-200">
        No resume content available to preview.
      </div>
    );
  }

  const { content, target_role } = resume;
  const personal = content.personal || {};
  const isClassic = template === 'classic';

  return (
    <div className="w-full flex justify-center py-4 overflow-x-auto">
      <div
        className={`w-full max-w-3xl bg-white shadow-md border border-slate-200 p-8 sm:p-12 text-slate-800 transition-all ${
          isClassic ? 'font-serif' : 'font-sans'
        }`}
        style={{ minHeight: '1000px' }}
      >
        {/* Header */}
        <header className={`mb-6 ${isClassic ? 'text-center' : 'text-left'}`}>
          <h1
            className={`text-2xl sm:text-3xl font-bold tracking-tight ${
              isClassic ? 'text-slate-900' : 'text-slate-900 tracking-normal'
            }`}
          >
            {personal.full_name || 'Candidate Name'}
          </h1>

          {target_role && (
            <p
              className={`text-sm sm:text-base font-semibold mt-1 ${
                isClassic ? 'text-slate-700 italic' : 'text-indigo-600'
              }`}
            >
              {target_role}
            </p>
          )}

          <div
            className={`flex flex-wrap items-center text-xs sm:text-sm text-slate-600 mt-2 gap-x-3 gap-y-1 ${
              isClassic ? 'justify-center' : 'justify-start'
            }`}
          >
            {personal.email && <span>{personal.email}</span>}
            {personal.phone && <span>• {personal.phone}</span>}
            {personal.location && <span>• {personal.location}</span>}
            {personal.linkedin_url && (
              <span>
                •{' '}
                <a
                  href={personal.linkedin_url}
                  target="_blank"
                  rel="noreferrer"
                  className="hover:underline text-blue-600"
                >
                  LinkedIn
                </a>
              </span>
            )}
            {personal.github_url && (
              <span>
                •{' '}
                <a
                  href={personal.github_url}
                  target="_blank"
                  rel="noreferrer"
                  className="hover:underline text-blue-600"
                >
                  GitHub
                </a>
              </span>
            )}
          </div>
        </header>

        {/* Professional Summary */}
        {content.summary && (
          <section className="mb-6">
            <h2
              className={`text-xs font-bold uppercase tracking-wider pb-1 mb-2 border-b ${
                isClassic
                  ? 'text-slate-800 border-slate-400'
                  : 'text-indigo-700 border-slate-200'
              }`}
            >
              Professional Summary
            </h2>
            <p className="text-xs sm:text-sm leading-relaxed text-slate-700">
              {content.summary}
            </p>
          </section>
        )}

        {/* Technical Skills */}
        {content.skills && content.skills.length > 0 && (
          <section className="mb-6">
            <h2
              className={`text-xs font-bold uppercase tracking-wider pb-1 mb-2 border-b ${
                isClassic
                  ? 'text-slate-800 border-slate-400'
                  : 'text-indigo-700 border-slate-200'
              }`}
            >
              Technical Skills
            </h2>
            <div className="space-y-1.5 text-xs sm:text-sm">
              {content.skills.map((cat, idx) => (
                <div key={idx} className="flex flex-wrap items-baseline gap-1">
                  <span className="font-semibold text-slate-900">
                    {cat.category}:
                  </span>
                  <span className="text-slate-700">
                    {Array.isArray(cat.items) ? cat.items.join(', ') : ''}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Projects */}
        {content.projects && content.projects.length > 0 && (
          <section className="mb-6">
            <h2
              className={`text-xs font-bold uppercase tracking-wider pb-1 mb-2 border-b ${
                isClassic
                  ? 'text-slate-800 border-slate-400'
                  : 'text-indigo-700 border-slate-200'
              }`}
            >
              Key Projects
            </h2>
            <div className="space-y-4">
              {content.projects.map((proj, idx) => (
                <div key={idx} className="text-xs sm:text-sm">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <div className="flex items-baseline gap-2">
                      <span className="font-bold text-slate-900">
                        {proj.title}
                      </span>
                      {proj.tech_stack && proj.tech_stack.length > 0 && (
                        <span className="text-xs font-medium text-indigo-600">
                          [{proj.tech_stack.join(', ')}]
                        </span>
                      )}
                    </div>
                    {proj.link && (
                      <a
                        href={proj.link}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Project Link ↗
                      </a>
                    )}
                  </div>
                  {proj.description_bullets && proj.description_bullets.length > 0 && (
                    <ul className="list-disc list-outside ml-4 mt-1.5 space-y-1 text-slate-700">
                      {proj.description_bullets.map((b, bIdx) => (
                        <li key={bIdx} className="leading-snug">
                          {b}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Internships & Experience */}
        {((content.internships && content.internships.length > 0) ||
          (content.work_experience && content.work_experience.length > 0)) && (
          <section className="mb-6">
            <h2
              className={`text-xs font-bold uppercase tracking-wider pb-1 mb-2 border-b ${
                isClassic
                  ? 'text-slate-800 border-slate-400'
                  : 'text-indigo-700 border-slate-200'
              }`}
            >
              Experience & Internships
            </h2>
            <div className="space-y-4">
              {[...(content.internships || []), ...(content.work_experience || [])].map(
                (exp, idx) => (
                  <div key={idx} className="text-xs sm:text-sm">
                    <div className="flex flex-wrap items-baseline justify-between gap-1">
                      <div>
                        <span className="font-bold text-slate-900">{exp.role}</span>
                        {exp.company && (
                          <span className="text-slate-700"> | {exp.company}</span>
                        )}
                      </div>
                      {(exp.start_date || exp.end_date) && (
                        <span className="text-xs text-slate-500">
                          {exp.start_date || ''} - {exp.end_date || 'Present'}
                        </span>
                      )}
                    </div>
                    {exp.description_bullets && exp.description_bullets.length > 0 && (
                      <ul className="list-disc list-outside ml-4 mt-1.5 space-y-1 text-slate-700">
                        {exp.description_bullets.map((b, bIdx) => (
                          <li key={bIdx} className="leading-snug">
                            {b}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              )}
            </div>
          </section>
        )}

        {/* Education */}
        {content.education && content.education.length > 0 && (
          <section className="mb-6">
            <h2
              className={`text-xs font-bold uppercase tracking-wider pb-1 mb-2 border-b ${
                isClassic
                  ? 'text-slate-800 border-slate-400'
                  : 'text-indigo-700 border-slate-200'
              }`}
            >
              Education
            </h2>
            <div className="space-y-2">
              {content.education.map((edu, idx) => (
                <div
                  key={idx}
                  className="flex flex-wrap items-baseline justify-between text-xs sm:text-sm"
                >
                  <div>
                    <span className="font-bold text-slate-900">{edu.degree}</span>
                    <span className="text-slate-700">, {edu.institution}</span>
                  </div>
                  <div className="text-xs text-slate-600">
                    {edu.graduation_year && <span>{edu.graduation_year}</span>}
                    {edu.score !== null && edu.score !== undefined && (
                      <span className="ml-2 font-medium">
                        [{edu.score_type === 'cgpa' ? 'CGPA' : '%'}: {edu.score}]
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Certifications & Achievements */}
        {((content.certifications && content.certifications.length > 0) ||
          (content.achievements && content.achievements.length > 0)) && (
          <section className="mb-4">
            <h2
              className={`text-xs font-bold uppercase tracking-wider pb-1 mb-2 border-b ${
                isClassic
                  ? 'text-slate-800 border-slate-400'
                  : 'text-indigo-700 border-slate-200'
              }`}
            >
              Certifications & Achievements
            </h2>
            <ul className="list-disc list-outside ml-4 space-y-1 text-xs sm:text-sm text-slate-700">
              {content.certifications?.map((c, idx) => (
                <li key={`cert-${idx}`}>
                  <span className="font-semibold text-slate-900">{c.name}</span>
                  {c.issuer && <span> — {c.issuer}</span>}
                  {c.year && <span> ({c.year})</span>}
                </li>
              ))}
              {content.achievements?.map((ach, idx) => (
                <li key={`ach-${idx}`}>{ach}</li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}

