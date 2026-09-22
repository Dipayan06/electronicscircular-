// Resale listing service (FR-H) — PHASE 14: real backend.
import apiClient from './apiClient';

export async function getListings(filterType = 'all') {
  const res = await apiClient.get('/listings', { params: { type: filterType } });
  return res.data.data;
}

export async function getListing(id) {
  const res = await apiClient.get(`/listings/${id}`);
  return res.data.data;
}

export async function createListing({ device_id, title, type, price, condition, description }) {
  const res = await apiClient.post('/listings', {
    device_id: device_id || null, title, type, price: Number(price), condition, description,
  });
  return res.data.data;
}

// Simulated reservation/purchase (no real payment — FR-H4).
export async function reserveListing(id) {
  const res = await apiClient.put(`/listings/${id}/reserve`);
  return res.data.data;
}
