// Dashboard service (FR-K) — PHASE 14: real backend.
import apiClient from './apiClient';

export async function getDashboard() {
  const res = await apiClient.get('/dashboard');
  return res.data.data; // { stats, activity }
}
