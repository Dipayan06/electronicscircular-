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

// ---- Feature 1: email verification ----
export async function verifyEmail(code) {
  const res = await apiClient.post('/auth/verify-email', { code });
  return res.data.data; // updated user (is_verified: true)
}

export async function resendVerification() {
  const res = await apiClient.post('/auth/resend-verification');
  return res.data;
}

// Dev mode only (EMAIL_DEV_MODE on the server): fetch MY pending code, since no
// real email is sent. The server returns 404 when dev mode is off.
export async function getDevVerificationCode() {
  const res = await apiClient.get('/auth/dev/verification-code');
  return res.data.data.code;
}
