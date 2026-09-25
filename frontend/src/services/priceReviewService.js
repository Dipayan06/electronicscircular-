// Price-review workflow (Feature 4).
import apiClient from './apiClient';

// Admin only. status: 'PENDING' | 'APPROVED' | 'REJECTED' | undefined (all)
export async function getReviews(status) {
  const res = await apiClient.get('/price-reviews', { params: status ? { status } : {} });
  return res.data.data;
}

export async function getMyReviews() {
  const res = await apiClient.get('/price-reviews/mine');
  return res.data.data;
}

export async function approveReview(id, note) {
  const res = await apiClient.put(`/price-reviews/${id}/approve`, { note });
  return res.data.data;
}

export async function rejectReview(id, note) {
  const res = await apiClient.put(`/price-reviews/${id}/reject`, { note });
  return res.data.data;
}
