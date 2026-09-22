// Axios API client — the ONLY place in the app that talks HTTP (Phase 1 §1.2).
// Pages/components never call axios directly; they go through service modules
// that use this client. This keeps the "service-layer seam" clean so that in
// Phase 7+ we can swap stubbed behaviour for real backend calls in one place.

import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Storage key for the auth token (set for real in Phase 7).
export const TOKEN_KEY = 'cem_token';

// Request interceptor: attach the JWT as a Bearer token when present.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: unwrap the standard { success, data, message } envelope
// (Phase 0 §20) and surface a friendly error message (NFR-6).
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Session expired / invalid token → tell the app to log out. We skip the
    // auth endpoints so a failed login shows its own message instead.
    const url = error.config?.url || '';
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/register');
    if (error.response?.status === 401 && !isAuthCall) {
      window.dispatchEvent(new CustomEvent('cem:unauthorized'));
    }

    let message;
    if (error.response) {
      message = error.response.data?.message || `Request failed (${error.response.status})`;
    } else if (error.request) {
      // Request made but no response → server unreachable.
      message = 'Cannot reach the server. Please check your connection and try again.';
    } else {
      message = error.message || 'Something went wrong';
    }
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
