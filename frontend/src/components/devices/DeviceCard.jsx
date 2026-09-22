// DeviceCard (Phase 0 §14, Phase 2 W3).
import { Link } from 'react-router-dom';
import { Smartphone, Laptop, Tablet } from 'lucide-react';
import StatusBadge from '../ui/StatusBadge';
import { typeLabel } from '../../services/deviceService';

const ICON = { smartphone: Smartphone, laptop: Laptop, tablet: Tablet };
const WORKING = { working: 'Working', faulty: 'Faulty', not_working: 'Not working' };

export default function DeviceCard({ device }) {
  const Icon = ICON[device.type] || Smartphone;
  return (
    <div className="card">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 10 }}>
        <Icon size={22} color="var(--green)" />
        <div>
          <div style={{ fontWeight: 700 }}>{device.brand} {device.model}</div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{typeLabel(device.type)} · {device.purchase_year}</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
        <StatusBadge status={(WORKING[device.working_status] || device.working_status).toUpperCase().replace(' ', '_')} />
        {device.recommendation && <StatusBadge status={device.recommendation} />}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <Link className="btn btn-secondary" to={`/devices/${device.id}`}>View</Link>
        <Link className="btn btn-secondary" to={`/devices/${device.id}/assessment`}>Assess</Link>
      </div>
    </div>
  );
}
