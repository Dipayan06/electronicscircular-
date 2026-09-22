// Quotations (Phase 2 W6, FR-F). Role-aware after the Phase 14 integration:
// a consumer sees their quotes and can accept/reject + book; a provider sees the
// requests directed to them and can submit a quote. The backend enforces both.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import useAsync from '../hooks/useAsync';
import { getQuotations, respondToQuote, submitQuote } from '../services/quotationService';
import { createBooking } from '../services/bookingService';
import StatusBadge from '../components/ui/StatusBadge';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';
import EmptyState from '../components/ui/EmptyState';

const PROVIDER_ROLES = ['provider', 'refurbisher', 'recycler', 'supplier'];

export default function QuotationsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const isProvider = PROVIDER_ROLES.includes(user?.role);
  const { data, loading, error, reload } = useAsync(getQuotations);

  const [booking, setBooking] = useState(null);
  const [form, setForm] = useState({ date: '', address: '', notes: '' });
  const [busy, setBusy] = useState(false);

  async function accept(q) {
    try {
      await respondToQuote(q.id, true);
      setForm({ date: new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 10), address: '', notes: '' });
      setBooking(q);
    } catch (err) { toast.error(err.message); }
  }
  async function reject(q) {
    try { await respondToQuote(q.id, false); reload(); } catch (err) { toast.error(err.message); }
  }

  // Provider action: submit a quote for a pending request.
  async function provideQuote(q) {
    try {
      await submitQuote(q.id, { cost: 2500, days: 3, description: 'Estimated repair cost' });
      toast.success('Quote sent');
      reload();
    } catch (err) { toast.error(err.message); }
  }

  async function confirmBooking() {
    setBusy(true);
    try {
      await createBooking({
        quotation_id: booking.id, date: form.date, service_type: 'Repair',
        address: form.address, notes: form.notes,
      });
      toast.success('Booking confirmed');
      setBooking(null);
      navigate('/bookings');
    } catch (err) {
      toast.error(err.message);
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 760 }}>
      <h1 className="page-title">Quotations</h1>
      <p className="page-sub">
        {isProvider ? 'Requests directed to you — submit a quote.' : 'Request quotes, then accept the one that fits.'}
      </p>

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {data && data.length === 0 && (
        <EmptyState
          title="No quotations yet"
          hint={isProvider ? 'Requests from customers will appear here.' : 'Request a quote from a provider to see it here.'}
          action={!isProvider && <Button onClick={() => navigate('/providers')}>Find providers</Button>}
        />
      )}

      {data && data.map((q) => (
        <div className="card" key={q.id} style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <strong style={{ flex: 1 }}>{q.device?.brand} {q.device?.model} · {q.provider?.name}</strong>
            <StatusBadge status={q.status} />
          </div>
          <p style={{ margin: '6px 0', color: 'var(--text-muted)' }}>"{q.problem}"</p>
          {q.status !== 'PENDING' && q.cost != null && (
            <p style={{ margin: '0 0 10px' }}>Estimate: <strong>₹{q.cost.toLocaleString('en-IN')}</strong> · {q.days} days</p>
          )}

          {/* Provider view */}
          {isProvider && q.status === 'PENDING' && (
            <Button onClick={() => provideQuote(q)}>Submit quote (₹2,500 · 3 days)</Button>
          )}
          {isProvider && q.status === 'SENT' && (
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Quote sent — awaiting the customer's response.</span>
          )}

          {/* Consumer view */}
          {!isProvider && q.status === 'PENDING' && (
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Awaiting the provider's quote…</span>
          )}
          {!isProvider && q.status === 'SENT' && (
            <div style={{ display: 'flex', gap: 8 }}>
              <Button variant="secondary" onClick={() => reject(q)}>Reject</Button>
              <Button onClick={() => accept(q)}>Accept → Book</Button>
            </div>
          )}
          {q.status === 'ACCEPTED' && <span style={{ fontSize: 13, color: 'var(--status-success)' }}>Accepted{!isProvider ? ' — see Bookings.' : '.'}</span>}
        </div>
      ))}

      <Modal
        open={!!booking}
        title="Create booking"
        onClose={() => setBooking(null)}
        footer={<>
          <Button variant="secondary" onClick={() => setBooking(null)}>Cancel</Button>
          <Button onClick={confirmBooking} disabled={!form.date || busy}>{busy ? 'Booking…' : 'Confirm booking'}</Button>
        </>}
      >
        <p style={{ marginTop: 0, color: 'var(--text-muted)' }}>
          {booking?.provider?.name} · {booking?.device?.brand} {booking?.device?.model}
        </p>
        <div className="field">
          <label>Preferred date</label>
          <input className="input" type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
        </div>
        <div className="field">
          <label>Pickup / drop-off address</label>
          <input className="input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} placeholder="Address" />
        </div>
        <div className="field">
          <label>Notes (optional)</label>
          <input className="input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </div>
      </Modal>
    </div>
  );
}
