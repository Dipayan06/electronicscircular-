// Material reference pricing (Feature 2) + price-band check (Feature 4).
import apiClient from './apiClient';

export async function getPrices() {
  const res = await apiClient.get('/pricing/materials');
  return res.data.data; // { items, feed_configured }
}

export async function getPriceHistory(material) {
  const res = await apiClient.get(`/pricing/materials/${material}/history`);
  return res.data.data;
}

// Admin only.
export async function setPrice(material, payload) {
  const res = await apiClient.put(`/pricing/materials/${material}`, payload);
  return res.data.data;
}

// Admin only. Fails with a clear message when no market feed is configured.
export async function refreshFromFeed() {
  const res = await apiClient.post('/pricing/refresh');
  return res.data.data;
}

// Advisory preview for the sell form; the server re-checks on submit.
export async function checkPrice({ kind, type, unit, price }) {
  const res = await apiClient.post('/pricing/check', { kind, type, unit, price });
  return res.data.data; // { level, reason, ratio, reference, regulated }
}
