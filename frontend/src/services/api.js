import axios from 'axios';
import { tokenStorage } from './token';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor: attach JWT access token
api.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 unauthorized & token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const originalRequest = error.config;
      // Do not redirect on login or register credential failures
      const isAuthEndpoint = originalRequest.url.includes('/auth/login') ||
                             originalRequest.url.includes('/auth/register');

      if (!isAuthEndpoint) {
        tokenStorage.removeToken();
        // Redirect to login if not already on the login page
        if (window.location.pathname !== '/login') {
          window.location.href = '/login?expired=true';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (userData) => api.post('/auth/register', userData),
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) => api.post('/auth/reset-password', { token, new_password: newPassword }),
  getMe: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data),
};

export const profileAPI = {
  getProfile: () => api.get('/profile'),
  saveProfile: (data) => api.put('/profile', data),
  uploadResume: (formData) => api.post('/profile/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000, // 30s for upload and AI extraction
  }),
  approveProfile: () => api.post('/profile/approve'),
  deleteProfile: () => api.delete('/profile'),
};

export const resumeAPI = {
  getRoles: () => api.get('/resumes/roles'),
  listResumes: () => api.get('/resumes'),
  getResume: (id) => api.get(`/resumes/${id}`),
  generateResume: (data) => api.post('/resumes/generate', data),
  generateMultipleResumes: (data) => api.post('/resumes/generate-multiple', data),
  updateResume: (id, data) => api.put(`/resumes/${id}`, data),
  duplicateResume: (id) => api.post(`/resumes/${id}/duplicate`),
  deleteResume: (id) => api.delete(`/resumes/${id}`),
  downloadResume: (id, format = 'pdf') =>
    api.get(`/resumes/${id}/download?format=${format}`, {
      responseType: 'blob',
    }),
};

export const jobAPI = {
  getSources: () => api.get('/jobs/sources'),
  discoverJobs: (params = {}) => api.post('/jobs/discover', params),
  listJobs: (params = {}) => api.get('/jobs', { params }),
  getJob: (jobId) => api.get(`/jobs/${jobId}`),
  saveJob: (jobId, notes = '') => api.post(`/jobs/${jobId}/save`, { notes }),
  unsaveJob: (jobId) => api.delete(`/jobs/${jobId}/save`),
  getSavedJobs: () => api.get('/jobs/saved'),
  updatePreferences: (preferences) => api.put('/jobs/preferences', preferences),
};

export const matchingAPI = {
  getMatch: (jobId, recomputeIfStale = false) =>
    api.get(`/matches/${jobId}`, { params: { recompute_if_stale: recomputeIfStale } }),
  computeMatch: (jobId, force = true) =>
    api.post(`/matches/${jobId}`, null, { params: { force } }),
  batchMatches: (jobIds) =>
    api.post('/matches/batch', { job_ids: jobIds }),
  getMyMatches: (params = {}) =>
    api.get('/matches', { params }),
  getRecommendedJobs: (params = {}) =>
    api.get('/jobs/recommended', { params }),
};

export const verificationAPI = {
  getVerification: (jobId) =>
    api.get(`/verification/${jobId}`),
  runVerification: (jobId) =>
    api.post(`/verification/${jobId}`),
  submitRecruiterDetails: (jobId, data) =>
    api.put(`/verification/${jobId}/recruiter`, data),
  reportJob: (jobId, data) =>
    api.post(`/verification/${jobId}/report`, data),
  listVerifications: (params = {}) =>
    api.get('/verification', { params }),
};

export default api;

