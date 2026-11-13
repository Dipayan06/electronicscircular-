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

// --- Product photos ---
export const MAX_PHOTOS = 5;
export const MAX_PHOTO_BYTES = 2 * 1024 * 1024;
export const PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

// Listing image urls are relative to the API base (works with /api or a full URL).
export function imageUrl(image) {
  return `${apiClient.defaults.baseURL}${image.url}`;
}

// files: File[]. Returns the updated listing (with its images).
export async function uploadListingImages(id, files) {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  // Clear the JSON default so the browser sets multipart/form-data with its boundary.
  const res = await apiClient.post(`/listings/${id}/images`, form, { headers: { 'Content-Type': undefined } });
  return res.data.data;
}

export async function deleteListingImage(id, imageId) {
  const res = await apiClient.delete(`/listings/${id}/images/${imageId}`);
  return res.data.data;
}
