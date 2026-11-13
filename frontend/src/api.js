// src/api.js — Attached with JWT Token Authorization header
import axios from 'axios';

const api = axios.create({ baseURL: '' });

// Automatically attach Bearer token to every request if user is logged in
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('mjm_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If session expires (401), clear token and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('mjm_token');
      localStorage.removeItem('mjm_user');
      window.dispatchEvent(new Event('authChange'));
    }
    return Promise.reject(error);
  }
);

export default api;
