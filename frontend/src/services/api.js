import axios from 'axios';

// Live production Render backend URL
const LIVE_RENDER_API = 'https://ai-career-agent-api-l4rh.onrender.com/api';

// Base API URL:
// 1. If VITE_API_BASE_URL is set (from Netlify env vars or .env), use it.
// 2. In production builds (on Netlify), default directly to the live Render cloud backend.
// 3. In local development (!import.meta.env.PROD), use '/api' to leverage Vite's local dev proxy.
let rawBase = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? LIVE_RENDER_API : '/api');
rawBase = rawBase.trim().replace(/\/+$/, '');
// Ensure it ends with /api if a full HTTP URL was provided without /api
if (rawBase.startsWith('http') && !rawBase.endsWith('/api')) {
  rawBase = `${rawBase}/api`;
}
const API_BASE = rawBase;

const API = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT Bearer Token if available
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor: Redirect to login on 401
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token if expired
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_data');
    }
    return Promise.reject(error);
  }
);

export default API;
