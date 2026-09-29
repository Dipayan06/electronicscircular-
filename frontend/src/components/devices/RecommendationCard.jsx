// RecommendationCard — displays the circularity recommendation (Phase 2 W4, FR-D).
// Shows action, reason and next step. The decision is the rule engine's; the
// optional "Explain in detail" text is written by the in-house language model.
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Wrench, RefreshCw, Recycle, Repeat, Tag, Sparkles } from 'lucide-react';
import { explainRecommendation } from '../../services/assistantService';

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
  const [explain, setExplain] = useState(null); // { explanation, source } | { error }
  const [explaining, setExplaining] = useState(false);

  async function loadExplanation() {
    setExplaining(true);
    try {
      setExplain(await explainRecommendation(deviceId));
    } catch (err) {
      setExplain({ error: err.message });
    } finally {
      setExplaining(false);
    }
  }

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

      {explain && (
        <div className="assist-explain" role="status">
          {explain.error ? explain.error : explain.explanation}
          {explain.source && explain.source !== 'model' && (
            <div className="assist-note" style={{ marginTop: 6 }}>The assistant wasn't confident, so this is the rule engine's own wording.</div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Link className="btn btn-primary" to={meta.to}>{meta.cta} →</Link>
        <Link className="btn btn-secondary" to={`/lifecycle/${deviceId}`}>View Lifecycle</Link>
        {!explain && (
          <button type="button" className="btn btn-ghost" onClick={loadExplanation} disabled={explaining}>
            <Sparkles size={15} /> {explaining ? 'Writing…' : 'Explain in detail'}
          </button>
        )}
      </div>

      <div className="placeholder-note" style={{ marginTop: 14 }}>
        Decided by a transparent rule-based engine, not AI. The detailed explanation is written by a small
        in-house language model; it describes the decision but never changes it.
      </div>
    </div>
  );
}
