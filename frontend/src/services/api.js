import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api',
});

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
