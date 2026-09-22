// Bookings (Phase 2, FR-G). Consumer sees bookings + status; the provider action
// (advance status) is exposed here as a demo control so the full repair flow —
// CONFIRMED → IN_PROGRESS → COMPLETED — is demonstrable end to end.
import useAsync from '../hooks/useAsync';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../context/ToastContext';
import { getBookings, updateBookingStatus, BOOKING_FLOW } from '../services/bookingService';
import StatusBadge from '../components/ui/StatusBadge';
import StatusStepper from '../components/ui/StatusStepper';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';
import EmptyState from '../components/ui/EmptyState';

export default function BookingsPage() {
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(getBookings);
  const toast = useToast();

  async function advance(b) {
    const next = BOOKING_FLOW[BOOKING_FLOW.indexOf(b.status) + 1];
    if (!next) return;
    try {
      await updateBookingStatus(b.id, next);
      reload();
    } catch (err) {
      toast.error(err.message);
    }
  }

  return (
    <div style={{ maxWidth: 760 }}>
      <h1 className="page-title">Bookings</h1>
      <p className="page-sub">Track your repair bookings from confirmation to completion.</p>

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {data && data.length === 0 && (
        <EmptyState title="No bookings yet" hint="Accept a quotation to create your first booking."
          action={<Button onClick={() => navigate('/quotations')}>Go to quotations</Button>} />
      )}

      {data && data.map((b) => {
        const isLast = b.status === 'COMPLETED';
        return (
          <div className="card" key={b.id} style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <strong style={{ flex: 1 }}>{b.device?.brand} {b.device?.model} · {b.provider?.name}</strong>
              <StatusBadge status={b.status} />
            </div>
            <StatusStepper steps={BOOKING_FLOW} current={b.status} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 30 }}>
              <span style={{ fontSize: 13, color: 'var(--text-muted)', flex: 1 }}>
                {b.date} · {b.service_type}{b.address ? ` · ${b.address}` : ''}
              </span>
              {!isLast && <Button variant="ghost" onClick={() => advance(b)}>Advance status (provider)</Button>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
