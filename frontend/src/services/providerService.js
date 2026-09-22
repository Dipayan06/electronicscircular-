// Provider service (FR-E) — PHASE 14: real backend.
import apiClient from './apiClient';

const TYPE_LABEL = {
  technician: 'Repair Technician',
  refurbisher: 'Refurbisher',
  recycler: 'Recycler / Collector',
  supplier: 'Spare-Part Supplier',
};
export const providerTypeLabel = (t) => TYPE_LABEL[t] || t;

export async function getProviders(filterType = 'all') {
  const res = await apiClient.get('/providers', { params: { type: filterType } });
  return res.data.data;
}

export async function getProvider(id) {
  const res = await apiClient.get(`/providers/${id}`);
  return res.data.data;
}

export async function verifyProvider(id) {
  const res = await apiClient.put(`/providers/${id}/verify`);
  return res.data.data;
}
