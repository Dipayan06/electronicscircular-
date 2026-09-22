// Provider profile (Phase 2 W5 → :id, FR-E2).
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, Star, BadgeCheck, Mail, MapPin } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { getProvider, providerTypeLabel } from '../services/providerService';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

export default function ProviderDetailPage() {
  const { id } = useParams();
  const { data: p, loading, error, reload } = useAsync(() => getProvider(id), [id]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;

  return (
    <div style={{ maxWidth: 640 }}>
      <Link to="/providers" className="back-link"><ChevronLeft size={16} /> Back to providers</Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{p.name}</h1>
        {p.verified && <span className="badge" style={{ color: 'var(--status-success)', background: 'var(--status-success-bg)' }}><BadgeCheck size={13} /> Verified</span>}
      </div>
      <p className="page-sub">{providerTypeLabel(p.type)}</p>

      <div className="card">
        <dl className="kv">
          <dt><MapPin size={14} style={{ verticalAlign: -2 }} /> Location</dt><dd>{p.location}</dd>
          <dt><Star size={14} style={{ verticalAlign: -2 }} /> Rating</dt><dd>{p.rating.toFixed(1)} / 5</dd>
          <dt><Mail size={14} style={{ verticalAlign: -2 }} /> Contact</dt><dd>{p.contact}</dd>
          <dt>Services</dt><dd>{p.services.join(', ')}</dd>
          <dt>Status</dt><dd>{p.verified ? 'Verified provider' : 'Pending verification'}</dd>
        </dl>
      </div>
    </div>
  );
}
