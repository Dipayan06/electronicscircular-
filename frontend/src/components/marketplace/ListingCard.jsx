// ListingCard — renders a device, component or material listing.
import { Link } from 'react-router-dom';
import { Smartphone, Laptop, Tablet, Cpu, MemoryStick, HardDrive, Fan, CircuitBoard, Boxes, Package } from 'lucide-react';
import StatusBadge from '../ui/StatusBadge';
import { categoryLabel } from '../../config/listings.config';

const ICON = {
  smartphone: Smartphone, laptop: Laptop, tablet: Tablet,
  cpu: Cpu, gpu: CircuitBoard, ram: MemoryStick, motherboard: CircuitBoard,
  storage: HardDrive, cooler: Fan, // materials + other fall back below
};

function iconFor(listing) {
  if (listing.kind === 'material') return Boxes;
  return ICON[listing.type] || Package;
}

export default function ListingCard({ listing }) {
  const Icon = iconFor(listing);
  const isMaterial = listing.kind === 'material';
  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <Icon size={20} color="var(--green)" />
        <strong style={{ flex: 1 }}>{listing.title}</strong>
      </div>

      <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--green-dark)' }}>
        ₹{listing.price.toLocaleString('en-IN')}{isMaterial ? <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}> / {listing.unit}</span> : null}
      </div>

      <div style={{ fontSize: 13, color: 'var(--text-muted)', margin: '4px 0 12px' }}>
        <span className="badge" style={{ background: 'var(--green-soft)', color: 'var(--green-dark)', marginRight: 6 }}>{categoryLabel(listing.type)}</span>
        {isMaterial
          ? <>{listing.quantity?.toLocaleString('en-IN')} {listing.unit} available{listing.min_order ? ` · min ${listing.min_order}${listing.unit}` : ''}</>
          : <>{listing.condition} · {listing.seller}</>}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Link className="btn btn-secondary" to={`/marketplace/${listing.id}`}>View</Link>
        <StatusBadge status={listing.status} />
      </div>
    </div>
  );
}
