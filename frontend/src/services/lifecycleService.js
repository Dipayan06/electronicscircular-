// Lifecycle / Digital Device Passport service (FR-J) — PHASE 14: real backend.
import apiClient from './apiClient';

export async function getLifecycle(deviceId) {
  const res = await apiClient.get(`/devices/${deviceId}/lifecycle`);
  return res.data.data;
}
