// Circular assistant — the in-house small language model (backend/app/ml).
// It helps with wording; decisions still come from the rule engine.
import apiClient from './apiClient';

export async function getAssistantStatus() {
  const res = await apiClient.get('/assistant/status');
  return res.data.data;
}

// → { reply, source: 'model' | 'fallback', confidence }
export async function askAssistant(message) {
  const res = await apiClient.post('/assistant/chat', { message });
  return res.data.data;
}

// Free-text fault description → { assessment: { screen, battery, body, powers_on, charging, water_damage }, source }
export async function parseAssessment(text) {
  const res = await apiClient.post('/assistant/parse-assessment', { text });
  return res.data.data;
}

// → { explanation, source, recommendation }
export async function explainRecommendation(deviceId) {
  const res = await apiClient.post('/assistant/explain', { device_id: Number(deviceId) });
  return res.data.data;
}

// → { title, description, source }
export async function draftListing(deviceId) {
  const res = await apiClient.post('/assistant/listing-draft', { device_id: Number(deviceId) });
  return res.data.data;
}
