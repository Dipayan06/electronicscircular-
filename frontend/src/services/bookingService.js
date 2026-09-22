// Booking service (FR-G) — PHASE 14: real backend.
import apiClient from './apiClient';

export const BOOKING_FLOW = ['REQUESTED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED'];

export async function getBookings() {
  const res = await apiClient.get('/bookings');
  return res.data.data;
}

// Created from an accepted quote (FR-G1). Backend derives device/provider from the quote.
export async function createBooking({ quotation_id, date, service_type, address, notes }) {
  const res = await apiClient.post('/bookings', { quotation_id, date, service_type, address, notes });
  return res.data.data;
}

export async function updateBookingStatus(id, status) {
  const res = await apiClient.put(`/bookings/${id}/status`, { status });
  return res.data.data;
}
