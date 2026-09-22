// RecommendationCard — displays the circularity recommendation (Phase 2 W4, FR-D).
// Shows action, reason and next step. Transparent, explainable — NOT called AI.
import { Link } from 'react-router-dom';
import { Wrench, RefreshCw, Recycle, Repeat, Tag } from 'lucide-react';

const META = {
  REPAIR:    { icon: Wrench,    color: 'var(--status-progress)', to: '/providers', cta: 'Find Repair Providers' },
  REUSE:     { icon: Repeat,    color: 'var(--status-success)',  to: '/devices',   cta: 'Back to My Devices' },
  RESALE:    { icon: Tag,       color: 'var(--status-success)',  to: '/list-device', cta: 'List on Marketplace' },
  REFURBISH: { icon: RefreshCw, color: 'var(--status-pending)',  to: '/providers', cta: 'Find a Refurbisher' },
  RECYCLE:   { icon: Recycle,   color: 'var(--status-danger)',   to: '/collection', cta: 'Request Collection' },
};

export default function RecommendationCard({ recommendation, deviceId }) {
  const { action, priority, reason, nextStep } = recommendation;
  const meta = META[action] || META.REPAIR;
  const Icon = meta.icon;

  return (
    <div className="card" style={{ borderLeft: `5px solid ${meta.color}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <Icon size={26} color={meta.color} />
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>RECOMMENDED ACTION</div>
          <div style={{ fontSize: 24, fontWeight: 800, color: meta.color }}>{action}</div>
        </div>
        <span className="badge" style={{ marginLeft: 'auto', color: 'var(--green-dark)', background: 'var(--green-soft)' }}>
          Circularity priority {priority}
        </span>
      </div>

      <p style={{ margin: '4px 0 6px', fontWeight: 600 }}>Why?</p>
      <p style={{ margin: '0 0 12px', color: 'var(--text)' }}>{reason}</p>

      <p style={{ margin: '0 0 4px', fontWeight: 600 }}>Next step</p>
      <p style={{ margin: '0 0 16px', color: 'var(--text-muted)' }}>{nextStep}</p>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Link className="btn btn-primary" to={meta.to}>{meta.cta} →</Link>
        <Link className="btn btn-secondary" to={`/lifecycle/${deviceId}`}>View Lifecycle</Link>
      </div>

      <div className="placeholder-note" style={{ marginTop: 14 }}>
        Transparent rule-based engine (not AI). The authoritative version runs on the backend in Phase 9.
      </div>
    </div>
  );
}
