// ListingCard (Phase 2 W7).
import { Link } from 'react-router-dom';
import { Smartphone, Laptop, Tablet } from 'lucide-react';
import StatusBadge from '../ui/StatusBadge';

const ICON = { smartphone: Smartphone, laptop: Laptop, tablet: Tablet };

export default function ListingCard({ listing }) {
  const Icon = ICON[listing.type] || Smartphone;
  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <Icon size={20} color="var(--green)" />
        <strong style={{ flex: 1 }}>{listing.title}</strong>
      </div>
      <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--green-dark)' }}>
        ₹{listing.price.toLocaleString('en-IN')}
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-muted)', margin: '4px 0 12px' }}>
        {listing.condition} · {listing.seller}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Link className="btn btn-secondary" to={`/marketplace/${listing.id}`}>View</Link>
        <StatusBadge status={listing.status} />
      </div>
    </div>
  );
}
