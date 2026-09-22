// Digital Device Passport (Phase 2 W9, FR-J). ★ signature demonstration screen.
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { getDevice } from '../services/deviceService';
import { getLifecycle } from '../services/lifecycleService';
import LifecycleTimeline from '../components/lifecycle/LifecycleTimeline';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

export default function LifecyclePage() {
  const { deviceId } = useParams();
  const { data: device } = useAsync(() => getDevice(deviceId), [deviceId]);
  const { data: events, loading, error, reload } = useAsync(() => getLifecycle(deviceId), [deviceId]);

  return (
    <div style={{ maxWidth: 680 }}>
      <Link to={`/devices/${deviceId}`} className="back-link"><ChevronLeft size={16} /> Back to device</Link>
      <h1 className="page-title">Digital Device Passport</h1>
      <p className="page-sub">
        {device ? `${device.brand} ${device.model} · Serial ${device.serial || 'N/A'}` : 'Complete lifecycle history'}
      </p>

      <div className="card">
        {loading && <LoadingState />}
        {error && <ErrorMessage message={error} onRetry={reload} />}
        {events && <LifecycleTimeline events={events} />}
        <div className="placeholder-note" style={{ marginTop: 10 }}>
          Every event is read from the database (lifecycle_events) — never hardcoded (FR-J4).
        </div>
      </div>
    </div>
  );
}
