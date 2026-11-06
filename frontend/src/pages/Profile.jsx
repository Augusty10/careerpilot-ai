import React, { useState, useEffect } from 'react';
import { profileAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import CompletenessBar from '../components/CompletenessBar';
import ResumeUploadCard from '../components/ResumeUploadCard';
import SkillTagInput from '../components/SkillTagInput';
import Input from '../components/Input';
import Button from '../components/Button';
import Alert from '../components/Alert';

export const Profile = () => {
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [approveLoading, setApproveLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [activeTab, setActiveTab] = useState('personal');
  const [isAiExtracted, setIsAiExtracted] = useState(false);

  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [validationErrors, setValidationErrors] = useState({});

  // Master profile state matching schema
  const [profile, setProfile] = useState({
    personal: {
      full_name: '',
      email: '',
      phone: '',
      location: '',
      linkedin_url: '',
      github_url: '',
    },
    education: [],
    skills: {
      languages: [],
      frameworks: [],
      databases: [],
      tools: [],
      other: [],
    },
    projects: [],
    internships: [],
    certifications: [],
    achievements: [],
    work_experience: [],
    preferred_roles: [],
    preferred_locations: [],
    profile_status: 'draft',
    completeness: 0,
  });

  // Fetch initial profile
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await profileAPI.getProfile();
        if (response.data && response.data.profile) {
          const loaded = response.data.profile;
          setProfile((prev) => ({
            ...prev,
            ...loaded,
            personal: {
              ...prev.personal,
              ...(loaded.personal || {}),
              full_name: loaded.personal?.full_name || user?.name || '',
              email: loaded.personal?.email || user?.email || '',
            },
            skills: {
              ...prev.skills,
              ...(loaded.skills || {}),
            },
          }));
        }
      } catch (err) {
        setErrorMessage('Failed to load profile. Please refresh.');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [user]);

  // Handle AI Resume Extraction auto-population
  const handleExtractionSuccess = (extractedData) => {
    setIsAiExtracted(true);
    setSuccessMessage('Resume parsed successfully! Review the extracted details below.');

    setProfile((prev) => ({
      ...prev,
      personal: {
        ...prev.personal,
        ...(extractedData.personal || {}),
        full_name: extractedData.personal?.full_name || prev.personal.full_name || user?.name || '',
        email: extractedData.personal?.email || prev.personal.email || user?.email || '',
      },
      education: extractedData.education?.length ? extractedData.education : prev.education,
      skills: {
        languages: extractedData.skills?.languages || prev.skills.languages,
        frameworks: extractedData.skills?.frameworks || prev.skills.frameworks,
        databases: extractedData.skills?.databases || prev.skills.databases,
        tools: extractedData.skills?.tools || prev.skills.tools,
        other: extractedData.skills?.other || prev.skills.other,
      },
      projects: extractedData.projects?.length ? extractedData.projects : prev.projects,
      internships: extractedData.internships?.length ? extractedData.internships : prev.internships,
      certifications: extractedData.certifications?.length ? extractedData.certifications : prev.certifications,
      achievements: extractedData.achievements?.length ? extractedData.achievements : prev.achievements,
      work_experience: extractedData.work_experience?.length ? extractedData.work_experience : prev.work_experience,
      preferred_roles: extractedData.preferred_roles?.length ? extractedData.preferred_roles : prev.preferred_roles,
      preferred_locations: extractedData.preferred_locations?.length ? extractedData.preferred_locations : prev.preferred_locations,
      profile_status: 'draft',
    }));

    window.scrollTo({ top: 350, behavior: 'smooth' });
  };

  // Helpers for Personal Info changes
  const handlePersonalChange = (e) => {
    const { name, value } = e.target;
    setProfile((prev) => ({
      ...prev,
      personal: { ...prev.personal, [name]: value },
    }));
    if (validationErrors[name]) {
      setValidationErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  // Helpers for Dynamic Lists
  const addEducation = () => {
    setProfile((prev) => ({
      ...prev,
      education: [
        ...prev.education,
        { degree: '', institution: '', graduation_year: 2024, score_type: 'cgpa', score: '' },
      ],
    }));
  };

  const updateEducation = (index, field, value) => {
    setProfile((prev) => {
      const updated = [...prev.education];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, education: updated };
    });
  };

  const removeEducation = (index) => {
    setProfile((prev) => ({
      ...prev,
      education: prev.education.filter((_, idx) => idx !== index),
    }));
  };

  const addProject = () => {
    setProfile((prev) => ({
      ...prev,
      projects: [
        ...prev.projects,
        { title: '', description: '', tech_stack: [], link: '' },
      ],
    }));
  };

  const updateProject = (index, field, value) => {
    setProfile((prev) => {
      const updated = [...prev.projects];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, projects: updated };
    });
  };

  const removeProject = (index) => {
    setProfile((prev) => ({
      ...prev,
      projects: prev.projects.filter((_, idx) => idx !== index),
    }));
  };

  const addInternship = () => {
    setProfile((prev) => ({
      ...prev,
      internships: [
        ...prev.internships,
        { company: '', role: '', start_date: '', end_date: '', description: '' },
      ],
    }));
  };

  const updateInternship = (index, field, value) => {
    setProfile((prev) => {
      const updated = [...prev.internships];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, internships: updated };
    });
  };

  const removeInternship = (index) => {
    setProfile((prev) => ({
      ...prev,
      internships: prev.internships.filter((_, idx) => idx !== index),
    }));
  };

  const addCertification = () => {
    setProfile((prev) => ({
      ...prev,
      certifications: [
        ...prev.certifications,
        { name: '', issuer: '', year: new Date().getFullYear() },
      ],
    }));
  };

  const updateCertification = (index, field, value) => {
    setProfile((prev) => {
      const updated = [...prev.certifications];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, certifications: updated };
    });
  };

  const removeCertification = (index) => {
    setProfile((prev) => ({
      ...prev,
      certifications: prev.certifications.filter((_, idx) => idx !== index),
    }));
  };

  // Validation
  const validateForm = () => {
    const errs = {};
    if (!profile.personal.full_name?.trim()) {
      errs.full_name = 'Full name is required';
    }
    if (!profile.personal.email?.trim()) {
      errs.email = 'Email address is required';
    }

    setValidationErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // Save Draft
  const handleSaveDraft = async () => {
    if (!validateForm()) {
      setActiveTab('personal');
      setErrorMessage('Please fix the validation errors before saving.');
      return;
    }

    setSaveLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const payload = { ...profile, profile_status: 'draft' };
      const response = await profileAPI.saveProfile(payload);
      if (response.data && response.data.profile) {
        setProfile(response.data.profile);
        setSuccessMessage('Draft profile saved successfully!');
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.error || 'Failed to save profile draft.');
    } finally {
      setSaveLoading(false);
    }
  };

  // Approve & Save Master Profile
  const handleApprove = async () => {
    if (!validateForm()) {
      setActiveTab('personal');
      setErrorMessage('Please fill in required personal details before approval.');
      return;
    }

    setApproveLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      // 1. Save profile
      await profileAPI.saveProfile({ ...profile });
      // 2. Approve
      const response = await profileAPI.approveProfile();
      if (response.data && response.data.profile) {
        setProfile(response.data.profile);
        setSuccessMessage('🎉 Master Career Profile approved! It is now the verified source of truth.');
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.error || 'Failed to approve master profile.');
    } finally {
      setApproveLoading(false);
    }
  };

  // Delete Profile
  const handleDeleteProfile = async () => {
    if (!window.confirm('Are you sure you want to delete your Master Profile and private resume files? This cannot be undone.')) {
      return;
    }

    setDeleteLoading(true);
    try {
      await profileAPI.deleteProfile();
      // Reload empty skeleton
      const res = await profileAPI.getProfile();
      if (res.data && res.data.profile) {
        setProfile(res.data.profile);
      }
      setSuccessMessage('Profile and private uploaded files deleted successfully.');
      setIsAiExtracted(false);
    } catch (err) {
      setErrorMessage('Failed to delete profile data.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const tabs = [
    { id: 'personal', label: '1. Personal' },
    { id: 'education', label: '2. Education' },
    { id: 'skills', label: '3. Skills' },
    { id: 'projects', label: '4. Projects' },
    { id: 'experience', label: '5. Internships & Work' },
    { id: 'certs', label: '6. Certs & Achievements' },
    { id: 'preferences', label: '7. Preferences' },
  ];

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center">
        <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
        <p className="mt-4 text-sm font-medium text-slate-500">Loading your master profile...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold mb-2">
            <span>CareerPilot AI</span>
            <span>•</span>
            <span>Module 2: Master Career Profile</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Master Career Profile
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            One single source of truth for all your upcoming AI-generated resumes and job applications.
          </p>
        </div>

        {/* Action Buttons Top */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="outline"
            onClick={handleSaveDraft}
            loading={saveLoading}
            size="md"
          >
            Save Draft
          </Button>

          <Button
            variant="primary"
            onClick={handleApprove}
            loading={approveLoading}
            size="md"
            className="shadow-md shadow-indigo-100"
          >
            Approve & Save Master Profile
          </Button>
        </div>
      </div>

      {/* Profile Strength & Completeness */}
      <CompletenessBar
        percentage={profile.completeness || 0}
        status={profile.profile_status || 'draft'}
      />

      {/* Notifications */}
      {successMessage && (
        <Alert
          type="success"
          message={successMessage}
          onClose={() => setSuccessMessage('')}
        />
      )}
      {errorMessage && (
        <Alert
          type="error"
          message={errorMessage}
          onClose={() => setErrorMessage('')}
        />
      )}

      {/* Resume Upload Card */}
      <ResumeUploadCard
        onExtractionSuccess={handleExtractionSuccess}
        isExtracted={isAiExtracted}
        onDismissBanner={() => setIsAiExtracted(false)}
      />

      {/* Multi-Section Form Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Navigation Tabs */}
        <div className="border-b border-slate-200 bg-slate-50/50 overflow-x-auto">
          <nav className="flex space-x-1 p-2 min-w-max" aria-label="Profile Sections">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-2 text-xs sm:text-sm font-semibold rounded-lg transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-white text-indigo-700 shadow-sm border border-slate-200'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6 sm:p-8">
          {/* TAB 1: PERSONAL DETAILS */}
          {activeTab === 'personal' && (
            <div className="space-y-6 max-w-3xl">
              <div>
                <h3 className="text-base font-bold text-slate-900">Personal Information</h3>
                <p className="text-xs text-slate-500">Contact details and portfolio links.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  id="full_name"
                  name="full_name"
                  label="Full Name"
                  placeholder="e.g. Alex Johnson"
                  value={profile.personal.full_name}
                  onChange={handlePersonalChange}
                  error={validationErrors.full_name}
                  required
                />

                <Input
                  id="email"
                  name="email"
                  label="Email Address"
                  type="email"
                  placeholder="alex@example.com"
                  value={profile.personal.email}
                  onChange={handlePersonalChange}
                  error={validationErrors.email}
                  required
                />

                <Input
                  id="phone"
                  name="phone"
                  label="Phone Number"
                  placeholder="e.g. +1 (555) 019-2834"
                  value={profile.personal.phone}
                  onChange={handlePersonalChange}
                  className={isAiExtracted && !profile.personal.phone ? 'border-amber-300' : ''}
                />

                <Input
                  id="location"
                  name="location"
                  label="Current City & Country"
                  placeholder="e.g. San Francisco, CA"
                  value={profile.personal.location}
                  onChange={handlePersonalChange}
                  className={isAiExtracted && !profile.personal.location ? 'border-amber-300' : ''}
                />

                <Input
                  id="linkedin_url"
                  name="linkedin_url"
                  label="LinkedIn Profile URL"
                  placeholder="https://linkedin.com/in/username"
                  value={profile.personal.linkedin_url || ''}
                  onChange={handlePersonalChange}
                />

                <Input
                  id="github_url"
                  name="github_url"
                  label="GitHub / Portfolio URL"
                  placeholder="https://github.com/username"
                  value={profile.personal.github_url || ''}
                  onChange={handlePersonalChange}
                />
              </div>
            </div>
          )}

          {/* TAB 2: EDUCATION */}
          {activeTab === 'education' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Education Background</h3>
                  <p className="text-xs text-slate-500">Degrees, institutions, and academic scores.</p>
                </div>
                <Button variant="outline" size="sm" onClick={addEducation}>
                  + Add Degree
                </Button>
              </div>

              {profile.education.length === 0 ? (
                <div className="p-8 text-center border-2 border-dashed border-slate-200 rounded-xl">
                  <p className="text-sm text-slate-500">No education entries added yet.</p>
                  <Button variant="outline" size="sm" onClick={addEducation} className="mt-3">
                    Add Education Entry
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {profile.education.map((edu, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3 relative">
                      <div className="flex justify-between items-center border-b border-slate-200/80 pb-2">
                        <span className="text-xs font-bold text-indigo-700 uppercase tracking-wide">
                          Education #{idx + 1}
                        </span>
                        <button
                          type="button"
                          onClick={() => removeEducation(idx)}
                          className="text-xs font-semibold text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <Input
                          id={`degree_${idx}`}
                          label="Degree / Major"
                          placeholder="e.g. B.Tech in Computer Science"
                          value={edu.degree}
                          onChange={(e) => updateEducation(idx, 'degree', e.target.value)}
                          required
                        />

                        <Input
                          id={`inst_${idx}`}
                          label="Institution / University"
                          placeholder="e.g. State University of Technology"
                          value={edu.institution}
                          onChange={(e) => updateEducation(idx, 'institution', e.target.value)}
                          required
                        />

                        <Input
                          id={`year_${idx}`}
                          label="Graduation Year"
                          type="number"
                          placeholder="e.g. 2024"
                          value={edu.graduation_year || ''}
                          onChange={(e) => updateEducation(idx, 'graduation_year', parseInt(e.target.value, 10) || null)}
                        />

                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                              Score Type
                            </label>
                            <select
                              value={edu.score_type || 'cgpa'}
                              onChange={(e) => updateEducation(idx, 'score_type', e.target.value)}
                              className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-600"
                            >
                              <option value="cgpa">CGPA (0 - 10)</option>
                              <option value="percentage">Percentage (0 - 100)</option>
                            </select>
                          </div>

                          <Input
                            id={`score_${idx}`}
                            label="Score"
                            type="number"
                            step="0.01"
                            placeholder={edu.score_type === 'cgpa' ? 'e.g. 8.7' : 'e.g. 85.5'}
                            value={edu.score ?? ''}
                            onChange={(e) => updateEducation(idx, 'score', parseFloat(e.target.value) || null)}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: SKILLS */}
          {activeTab === 'skills' && (
            <div className="space-y-6 max-w-4xl">
              <div>
                <h3 className="text-base font-bold text-slate-900">Categorized Skills</h3>
                <p className="text-xs text-slate-500">
                  Tag your technical competencies. Categorization helps our AI agents craft tailored resumes for specific job roles.
                </p>
              </div>

              <div className="space-y-4">
                <SkillTagInput
                  category="languages"
                  label="Programming Languages"
                  tags={profile.skills.languages || []}
                  onTagsChange={(tags) =>
                    setProfile((prev) => ({
                      ...prev,
                      skills: { ...prev.skills, languages: tags },
                    }))
                  }
                />

                <SkillTagInput
                  category="frameworks"
                  label="Frameworks & Libraries"
                  tags={profile.skills.frameworks || []}
                  onTagsChange={(tags) =>
                    setProfile((prev) => ({
                      ...prev,
                      skills: { ...prev.skills, frameworks: tags },
                    }))
                  }
                />

                <SkillTagInput
                  category="databases"
                  label="Databases & Storage"
                  tags={profile.skills.databases || []}
                  onTagsChange={(tags) =>
                    setProfile((prev) => ({
                      ...prev,
                      skills: { ...prev.skills, databases: tags },
                    }))
                  }
                />

                <SkillTagInput
                  category="tools"
                  label="Tools & Developer Platforms"
                  tags={profile.skills.tools || []}
                  onTagsChange={(tags) =>
                    setProfile((prev) => ({
                      ...prev,
                      skills: { ...prev.skills, tools: tags },
                    }))
                  }
                />

                <SkillTagInput
                  category="other"
                  label="Other Skills & Concepts (e.g. REST, Agile, System Design)"
                  tags={profile.skills.other || []}
                  onTagsChange={(tags) =>
                    setProfile((prev) => ({
                      ...prev,
                      skills: { ...prev.skills, other: tags },
                    }))
                  }
                />
              </div>
            </div>
          )}

          {/* TAB 4: PROJECTS */}
          {activeTab === 'projects' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Key Projects</h3>
                  <p className="text-xs text-slate-500">Academic and personal projects demonstrating your abilities.</p>
                </div>
                <Button variant="outline" size="sm" onClick={addProject}>
                  + Add Project
                </Button>
              </div>

              {profile.projects.length === 0 ? (
                <div className="p-8 text-center border-2 border-dashed border-slate-200 rounded-xl">
                  <p className="text-sm text-slate-500">No projects added yet.</p>
                  <Button variant="outline" size="sm" onClick={addProject} className="mt-3">
                    Add First Project
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {profile.projects.map((proj, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                      <div className="flex justify-between items-center border-b border-slate-200/80 pb-2">
                        <span className="text-xs font-bold text-indigo-700 uppercase tracking-wide">
                          Project #{idx + 1}
                        </span>
                        <button
                          type="button"
                          onClick={() => removeProject(idx)}
                          className="text-xs font-semibold text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <Input
                          id={`proj_title_${idx}`}
                          label="Project Title"
                          placeholder="e.g. CareerPilot AI Portal"
                          value={proj.title}
                          onChange={(e) => updateProject(idx, 'title', e.target.value)}
                          required
                        />

                        <Input
                          id={`proj_link_${idx}`}
                          label="Project Link / Repository"
                          placeholder="https://github.com/..."
                          value={proj.link || ''}
                          onChange={(e) => updateProject(idx, 'link', e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                          Project Description
                        </label>
                        <textarea
                          rows={3}
                          value={proj.description || ''}
                          onChange={(e) => updateProject(idx, 'description', e.target.value)}
                          placeholder="Describe the problem, your solution, and key impact..."
                          className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-600"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-600 mb-1">
                          Tech Stack (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={proj.tech_stack?.join(', ') || ''}
                          onChange={(e) =>
                            updateProject(
                              idx,
                              'tech_stack',
                              e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                            )
                          }
                          placeholder="e.g. React, Python, Flask, MongoDB"
                          className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 5: INTERNSHIPS & WORK EXPERIENCE */}
          {activeTab === 'experience' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Internships & Work Experience</h3>
                  <p className="text-xs text-slate-500">Industry internships, freelance gigs, or apprenticeships.</p>
                </div>
                <Button variant="outline" size="sm" onClick={addInternship}>
                  + Add Internship
                </Button>
              </div>

              {profile.internships.length === 0 ? (
                <div className="p-8 text-center border-2 border-dashed border-slate-200 rounded-xl">
                  <p className="text-sm text-slate-500">No internship entries added yet.</p>
                  <Button variant="outline" size="sm" onClick={addInternship} className="mt-3">
                    Add Internship
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {profile.internships.map((intern, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                      <div className="flex justify-between items-center border-b border-slate-200/80 pb-2">
                        <span className="text-xs font-bold text-indigo-700 uppercase tracking-wide">
                          Internship #{idx + 1}
                        </span>
                        <button
                          type="button"
                          onClick={() => removeInternship(idx)}
                          className="text-xs font-semibold text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <Input
                          id={`intern_comp_${idx}`}
                          label="Company Name"
                          placeholder="e.g. TechStart Labs"
                          value={intern.company}
                          onChange={(e) => updateInternship(idx, 'company', e.target.value)}
                          required
                        />

                        <Input
                          id={`intern_role_${idx}`}
                          label="Role / Title"
                          placeholder="e.g. Software Engineering Intern"
                          value={intern.role}
                          onChange={(e) => updateInternship(idx, 'role', e.target.value)}
                          required
                        />

                        <Input
                          id={`intern_start_${idx}`}
                          label="Start Date"
                          placeholder="e.g. Jun 2023"
                          value={intern.start_date || ''}
                          onChange={(e) => updateInternship(idx, 'start_date', e.target.value)}
                        />

                        <Input
                          id={`intern_end_${idx}`}
                          label="End Date"
                          placeholder="e.g. Aug 2023 or Present"
                          value={intern.end_date || ''}
                          onChange={(e) => updateInternship(idx, 'end_date', e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                          Responsibilities & Key Achievements
                        </label>
                        <textarea
                          rows={2}
                          value={intern.description || ''}
                          onChange={(e) => updateInternship(idx, 'description', e.target.value)}
                          placeholder="Summarize key tasks, tools used, and results achieved..."
                          className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-600"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 6: CERTS & ACHIEVEMENTS */}
          {activeTab === 'certs' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Certifications & Achievements</h3>
                  <p className="text-xs text-slate-500">Professional credentials, hackathon wins, honors.</p>
                </div>
                <Button variant="outline" size="sm" onClick={addCertification}>
                  + Add Certification
                </Button>
              </div>

              {/* Certifications List */}
              <div className="space-y-3">
                {profile.certifications.map((cert, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row items-start sm:items-center gap-3">
                    <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2 w-full">
                      <input
                        type="text"
                        placeholder="Certification Name"
                        value={cert.name}
                        onChange={(e) => updateCertification(idx, 'name', e.target.value)}
                        className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs"
                      />
                      <input
                        type="text"
                        placeholder="Issuing Organization"
                        value={cert.issuer || ''}
                        onChange={(e) => updateCertification(idx, 'issuer', e.target.value)}
                        className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs"
                      />
                      <input
                        type="number"
                        placeholder="Year"
                        value={cert.year || ''}
                        onChange={(e) => updateCertification(idx, 'year', parseInt(e.target.value, 10) || null)}
                        className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeCertification(idx)}
                      className="text-xs font-semibold text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>

              {/* Achievements */}
              <div className="pt-4 border-t border-slate-200">
                <SkillTagInput
                  category="achievements"
                  label="Honors & Key Achievements (Press Enter to add)"
                  tags={profile.achievements || []}
                  onTagsChange={(tags) =>
                    setProfile((prev) => ({
                      ...prev,
                      achievements: tags,
                    }))
                  }
                />
              </div>
            </div>
          )}

          {/* TAB 7: PREFERENCES */}
          {activeTab === 'preferences' && (
            <div className="space-y-6 max-w-3xl">
              <div>
                <h3 className="text-base font-bold text-slate-900">Career Preferences</h3>
                <p className="text-xs text-slate-500">
                  Target job roles and preferred cities. These guide future Job Discovery and Matching agents.
                </p>
              </div>

              <div className="space-y-4">
                <SkillTagInput
                  category="preferred_roles"
                  label="Target Job Roles (e.g. Frontend Engineer, Full Stack, Data Analyst)"
                  tags={profile.preferred_roles || []}
                  onTagsChange={(tags) =>
                    setProfile((prev) => ({
                      ...prev,
                      preferred_roles: tags,
                    }))
                  }
                />

                <SkillTagInput
                  category="preferred_locations"
                  label="Preferred Locations (e.g. Remote, San Francisco, New York, Bangalore)"
                  tags={profile.preferred_locations || []}
                  onTagsChange={(tags) =>
                    setProfile((prev) => ({
                      ...prev,
                      preferred_locations: tags,
                    }))
                  }
                />
              </div>
            </div>
          )}

          {/* Bottom Actions Bar */}
          <div className="mt-8 pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
            <button
              type="button"
              onClick={handleDeleteProfile}
              disabled={deleteLoading}
              className="text-xs font-semibold text-red-600 hover:text-red-800 hover:underline"
            >
              Delete Master Profile Data
            </button>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <Button
                variant="outline"
                onClick={handleSaveDraft}
                loading={saveLoading}
                className="flex-1 sm:flex-none"
              >
                Save Draft
              </Button>
              <Button
                variant="primary"
                onClick={handleApprove}
                loading={approveLoading}
                className="flex-1 sm:flex-none shadow-md shadow-indigo-100"
              >
                Approve & Save Master Profile
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;

