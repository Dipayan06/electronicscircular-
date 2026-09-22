// ProviderCard (Phase 0 §14, Phase 2 W5).
import { Link } from 'react-router-dom';
import { Wrench, RefreshCw, Recycle, Package, BadgeCheck, Star } from 'lucide-react';
import { providerTypeLabel } from '../../services/providerService';

const ICON = { technician: Wrench, refurbisher: RefreshCw, recycler: Recycle, supplier: Package };

export default function ProviderCard({ provider, onRequestQuote }) {
  const Icon = ICON[provider.type] || Wrench;
  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <Icon size={20} color="var(--green)" />
        <strong style={{ flex: 1 }}>{provider.name}</strong>
        {provider.verified
          ? <span className="badge" style={{ color: 'var(--status-success)', background: 'var(--status-success-bg)' }}><BadgeCheck size={13} /> Verified</span>
          : <span className="badge" style={{ color: 'var(--status-pending)', background: 'var(--status-pending-bg)' }}>Pending</span>}
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>
        {providerTypeLabel(provider.type)} · {provider.location}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, marginBottom: 8 }}>
        <Star size={14} color="#e0a800" fill="#e0a800" /> {provider.rating.toFixed(1)}
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 14 }}>
        {provider.services.slice(0, 3).join(' · ')}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <Link className="btn btn-secondary" to={`/providers/${provider.id}`}>View</Link>
        {onRequestQuote && <button className="btn btn-primary" onClick={() => onRequestQuote(provider)}>Request Quote</button>}
      </div>
    </div>
  );
}
