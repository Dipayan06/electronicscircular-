// Auth service (Phase 7). Talks to the REAL backend (FastAPI) via apiClient.
// This replaces the Phase 3 stub. Each function unwraps the { success, data,
// message } envelope and returns `data`; apiClient's interceptor already turns a
// failure envelope into a thrown Error with the server's message.
import apiClient from './apiClient';

export async function login(email, password) {
  const res = await apiClient.post('/auth/login', { email, password });
  return res.data.data; // { token, user }
}

export async function register({ name, email, password, role }) {
  const res = await apiClient.post('/auth/register', { name, email, password, role });
  return res.data.data; // { token, user }
}

export async function me() {
  const res = await apiClient.get('/auth/me');
  return res.data.data; // user
}
