// Collection & recycling service (FR-I) — PHASE 14: real backend.
import apiClient from './apiClient';

export const COLLECTION_FLOW = ['REQUESTED', 'SCHEDULED', 'PICKED_UP', 'RECEIVED', 'RECYCLED'];

export async function getCollections() {
  const res = await apiClient.get('/collections');
  return res.data.data;
}

export async function requestCollection({ device_id, collector_id, address, preferred_date }) {
  const res = await apiClient.post('/collections', { device_id, collector_id, address, preferred_date });
  return res.data.data;
}

export async function advanceCollection(id, status) {
  const res = await apiClient.put(`/collections/${id}/status`, { status });
  return res.data.data;
}
