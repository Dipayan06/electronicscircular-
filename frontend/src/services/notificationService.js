// Notification service (Feature 3) — the bell in the top bar reads from here.
import apiClient from './apiClient';

export async function getNotifications() {
  const res = await apiClient.get('/notifications');
  return res.data.data; // { items, unread }
}

export async function getUnreadCount() {
  const res = await apiClient.get('/notifications/unread-count');
  return res.data.data.unread;
}

export async function markRead(id) {
  const res = await apiClient.put(`/notifications/${id}/read`);
  return res.data.data;
}

export async function markAllRead() {
  const res = await apiClient.put('/notifications/read-all');
  return res.data.data;
}
