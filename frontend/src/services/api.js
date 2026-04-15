import axios from 'axios';

const API = axios.create({
  baseURL: `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api`,
  timeout: 120000, // 2 min — job search with AI can take a while
  headers: {
    'X-API-Key': process.env.REACT_APP_API_KEY || '',
  },
});

// Response interceptor: transform HTTP errors into friendly messages
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Network error — backend not running
      error.friendlyMessage = 'Cannot reach the server. Make sure the backend is running on port 8000.';
    } else {
      const status = error.response.status;
      const detail = error.response.data?.detail;

      if (status === 400) {
        error.friendlyMessage = detail || 'Invalid request. Check your inputs.';
      } else if (status === 404) {
        error.friendlyMessage = detail || 'Resource not found.';
      } else if (status === 422) {
        error.friendlyMessage = 'Validation error. Check your inputs.';
      } else if (status === 500) {
        error.friendlyMessage = 'Server error. Check the backend logs for details.';
      } else {
        error.friendlyMessage = detail || `Unexpected error (${status}).`;
      }
    }
    return Promise.reject(error);
  }
);

// Applications
export const getApplications = () => API.get('/applications');
export const createApplication = (data) => API.post('/applications', data);
export const updateApplication = (id, data) => API.patch(`/applications/${id}`, data);
export const deleteApplication = (id) => API.delete(`/applications/${id}`);

// Jobs
export const getJobs = () => API.get('/jobs');
export const searchJobs = (params) => API.post('/jobs/search', params);
export const applyToJob = (id) => API.post(`/jobs/${id}/apply`);

// Resume
export const uploadResume = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return API.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const getProfile = () => API.get('/resume/profile');

// Stats
export const getStats = () => API.get('/stats');
