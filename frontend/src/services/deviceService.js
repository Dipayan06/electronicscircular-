// Device service (FR-B, FR-C) — PHASE 14: now backed by the REAL backend.
// The mock is gone; every function calls the FastAPI endpoints via apiClient and
// unwraps the { success, data, message } envelope. The signatures are unchanged
// from the Phase 4 mock, so no page needed rewriting.
import apiClient from './apiClient';

const TYPE_LABEL = { smartphone: 'Smartphone', laptop: 'Laptop', tablet: 'Tablet' };
export const DEVICE_TYPES = Object.keys(TYPE_LABEL);
export const typeLabel = (t) => TYPE_LABEL[t] || t;

export async function getDevices() {
  const res = await apiClient.get('/devices');
  return res.data.data;
}

export async function getDevice(id) {
  const res = await apiClient.get(`/devices/${id}`);
  return res.data.data;
}

export async function createDevice(data) {
  const res = await apiClient.post('/devices', data);
  return res.data.data;
}

export async function updateDevice(id, patch) {
  const res = await apiClient.put(`/devices/${id}`, patch);
  return res.data.data;
}

export async function deleteDevice(id) {
  await apiClient.delete(`/devices/${id}`);
}

// Store an assessment and get the recommendation (FR-C + FR-D).
// Backend returns { recommendation: { action, priority, reason, nextStep } }.
export async function assessDevice(id, assessment) {
  const res = await apiClient.post(`/devices/${id}/assessment`, assessment);
  return res.data.data;
}
