// Resale-value estimate for devices and components.
import apiClient from './apiClient';

// { kind, type, device_id?, purchase_price?, purchase_year?, condition? }
export async function getEstimate(payload) {
  const res = await apiClient.post('/valuation/estimate', payload);
  return res.data.data;
}

export async function getCategoryPrices() {
  const res = await apiClient.get('/valuation/categories');
  return res.data.data;
}

// Admin only.
export async function updateCategoryPrice(category, payload) {
  const res = await apiClient.put(`/valuation/categories/${category}`, payload);
  return res.data.data;
}
