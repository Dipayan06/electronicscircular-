// Marketplace listing service (FR-H) — devices, components and materials.
import apiClient from './apiClient';

// filterKind: 'all' | 'device' | 'component' | 'material'
export async function getListings(filterKind = 'all') {
  const res = await apiClient.get('/listings', { params: { kind: filterKind } });
  return res.data.data;
}

export async function getListing(id) {
  const res = await apiClient.get(`/listings/${id}`);
  return res.data.data;
}

export async function createListing(payload) {
  const res = await apiClient.post('/listings', payload);
  return res.data.data;
}

// Buy/reserve. Materials pass a quantity (buy in appropriate amounts or bulk).
export async function reserveListing(id, quantity) {
  const res = await apiClient.put(`/listings/${id}/reserve`, quantity != null ? { quantity } : {});
  return res.data.data;
}

// The seller's own listings, including ones held for price review (Feature 4).
export async function getMyListings() {
  const res = await apiClient.get('/listings/mine');
  return res.data.data;
}
