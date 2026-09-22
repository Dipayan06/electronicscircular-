// My Devices (Phase 2 W3, FR-B3).
import { useNavigate } from 'react-router-dom';
import useAsync from '../hooks/useAsync';
import { getDevices } from '../services/deviceService';
import DeviceCard from '../components/devices/DeviceCard';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';
import EmptyState from '../components/ui/EmptyState';

export default function DevicesPage() {
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(getDevices);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 className="page-title">My Devices</h1>
          <p className="page-sub">Register and manage your smartphones, laptops and tablets.</p>
        </div>
        <Button onClick={() => navigate('/devices/new')}>+ Register Device</Button>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {data && data.length === 0 && (
        <EmptyState
          title="No devices yet"
          hint="Register your first device to start tracking its circular lifecycle."
          action={<Button onClick={() => navigate('/devices/new')}>Register a device</Button>}
        />
      )}
      {data && data.length > 0 && (
        <div className="grid grid-cards">
          {data.map((d) => <DeviceCard key={d.id} device={d} />)}
        </div>
      )}
    </div>
  );
}
