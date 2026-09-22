// Quotation service (FR-F) — PHASE 14: real backend.
import apiClient from './apiClient';

export async function getQuotations() {
  const res = await apiClient.get('/quotations');
  return res.data.data;
}

export async function requestQuotation({ device_id, provider_id, problem }) {
  const res = await apiClient.post('/quotations', { device_id, provider_id, problem });
  return res.data.data;
}

// Provider action: submit the estimate (PENDING → SENT).
export async function submitQuote(id, { cost, days, description }) {
  const res = await apiClient.put(`/quotations/${id}/quote`, { cost, days, description });
  return res.data.data;
}

// Consumer accepts / rejects (SENT → ACCEPTED | REJECTED).
export async function respondToQuote(id, accept) {
  const res = await apiClient.put(`/quotations/${id}/${accept ? 'accept' : 'reject'}`);
  return res.data.data;
}
