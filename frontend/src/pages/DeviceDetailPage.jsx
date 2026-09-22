// Device detail (Phase 2 W3 → :id, FR-B4) with a lifecycle tab.
import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getDevice, deleteDevice, typeLabel } from '../services/deviceService';
import { getLifecycle } from '../services/lifecycleService';
import Button from '../components/ui/Button';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';
import LifecycleTimeline from '../components/lifecycle/LifecycleTimeline';

const WORKING = { working: 'WORKING', faulty: 'FAULTY', not_working: 'NOT_WORKING' };

export default function DeviceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [tab, setTab] = useState('details');
  const { data: device, loading, error, reload } = useAsync(() => getDevice(id), [id]);
  const { data: events } = useAsync(() => getLifecycle(id), [id]);

  async function handleDelete() {
    if (!window.confirm('Remove this device? This cannot be undone.')) return;
    try {
      await deleteDevice(id);
      toast.success('Device removed');
      navigate('/devices');
    } catch (err) {
      toast.error(err.message);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  if (!device) return null;

  return (
    <div style={{ maxWidth: 760 }}>
      <Link to="/devices" className="back-link"><ChevronLeft size={16} /> Back to devices</Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{device.brand} {device.model}</h1>
        <StatusBadge status={WORKING[device.working_status] || 'WORKING'} />
        {device.recommendation && <StatusBadge status={device.recommendation} />}
      </div>
      <p className="page-sub">{typeLabel(device.type)} · Serial {device.serial || 'N/A'}</p>

      <div className="tabs">
        <button className={`tab ${tab === 'details' ? 'active' : ''}`} onClick={() => setTab('details')}>Details</button>
        <button className={`tab ${tab === 'lifecycle' ? 'active' : ''}`} onClick={() => setTab('lifecycle')}>Lifecycle</button>
      </div>

      {tab === 'details' && (
        <div className="card">
          <dl className="kv">
            <dt>Type</dt><dd>{typeLabel(device.type)}</dd>
            <dt>Brand</dt><dd>{device.brand}</dd>
            <dt>Model</dt><dd>{device.model}</dd>
            <dt>Serial / IMEI</dt><dd>{device.serial || '—'}</dd>
            <dt>Purchase year</dt><dd>{device.purchase_year}</dd>
            <dt>Working status</dt><dd style={{ textTransform: 'capitalize' }}>{device.working_status.replace('_', ' ')}</dd>
            <dt>Accessories</dt><dd>{device.accessories || '—'}</dd>
            <dt>Recommendation</dt><dd>{device.recommendation ? <StatusBadge status={device.recommendation} /> : 'Not assessed yet'}</dd>
          </dl>

          <div style={{ display: 'flex', gap: 8, marginTop: 18, flexWrap: 'wrap' }}>
            <Button onClick={() => navigate(`/devices/${id}/assessment`)}>Assess Condition</Button>
            <Button variant="secondary" onClick={() => navigate(`/lifecycle/${id}`)}>Digital Passport</Button>
            <Button variant="ghost" onClick={handleDelete}>Delete</Button>
          </div>
        </div>
      )}

      {tab === 'lifecycle' && (
        <div className="card">
          <LifecycleTimeline events={events || []} />
        </div>
      )}
    </div>
  );
}
