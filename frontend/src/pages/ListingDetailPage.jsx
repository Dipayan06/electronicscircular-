// Listing detail + simulated reservation (Phase 2 W7 → :id, FR-H4). No real payment.
import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getListing, reserveListing } from '../services/listingService';
import StatusBadge from '../components/ui/StatusBadge';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

export default function ListingDetailPage() {
  const { id } = useParams();
  const { data, loading, error, reload } = useAsync(() => getListing(id), [id]);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  async function reserve() {
    setBusy(true);
    try {
      await reserveListing(id);
      toast.success('Listing reserved');
      setConfirm(false);
      reload();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;

  return (
    <div style={{ maxWidth: 560 }}>
      <Link to="/marketplace" className="back-link"><ChevronLeft size={16} /> Back to marketplace</Link>
      <h1 className="page-title">{data.title}</h1>
      <div style={{ fontSize: 30, fontWeight: 800, color: 'var(--green-dark)', marginBottom: 12 }}>
        ₹{data.price.toLocaleString('en-IN')}
      </div>

      <div className="card">
        <dl className="kv">
          <dt>Condition</dt><dd>{data.condition}</dd>
          <dt>Seller</dt><dd>{data.seller}</dd>
          <dt>Status</dt><dd><StatusBadge status={data.status} /></dd>
          <dt>Description</dt><dd>{data.description}</dd>
        </dl>
        <div style={{ marginTop: 18 }}>
          {data.status === 'ACTIVE'
            ? <Button onClick={() => setConfirm(true)}>Reserve this device</Button>
            : <p style={{ color: 'var(--text-muted)', margin: 0 }}>This device is {data.status.toLowerCase()} and no longer available.</p>}
        </div>
        <div className="placeholder-note" style={{ marginTop: 14 }}>
          Simulated reservation — payment integration is out of scope for the prototype (Phase 0 §10).
        </div>
      </div>

      <Modal open={confirm} title="Confirm reservation" onClose={() => setConfirm(false)}
        footer={<>
          <Button variant="secondary" onClick={() => setConfirm(false)}>Cancel</Button>
          <Button onClick={reserve} disabled={busy}>{busy ? 'Reserving…' : 'Confirm'}</Button>
        </>}>
        <p style={{ margin: 0 }}>Reserve <strong>{data.title}</strong> for ₹{data.price.toLocaleString('en-IN')}? (No payment is taken in this prototype.)</p>
      </Modal>
    </div>
  );
}
