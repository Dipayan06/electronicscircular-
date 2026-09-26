// Estimated resale value shown while listing a device or component. Explains
// every factor behind the number and is clear that it is an estimate, not a
// market quote. "Use this price" copies the midpoint into the price field.
import { useState } from 'react';
import { TrendingUp, ChevronDown, ChevronUp } from 'lucide-react';
import { inr } from '../../utils/format';

const CONFIDENCE = { high: 'High confidence', medium: 'Medium confidence', low: 'Low confidence' };

export default function EstimateCard({ estimate, loading, onUse }) {
  const [open, setOpen] = useState(false);
  if (!estimate && !loading) return null;

  if (loading && !estimate) {
    return <div className="estimate-card"><span className="estimate-muted">Estimating resale value…</span></div>;
  }
  if (!estimate.available) {
    return (
      <div className="estimate-card">
        <div className="estimate-head"><TrendingUp size={16} /> Estimated resale value</div>
        <span className="estimate-muted">{estimate.reason}</span>
      </div>
    );
  }

  return (
    <div className="estimate-card" aria-live="polite">
      <div className="estimate-head">
        <TrendingUp size={16} /> Estimated resale value
        <span className={`estimate-conf ${estimate.confidence}`}>{CONFIDENCE[estimate.confidence]}</span>
      </div>
      <div className="estimate-range">
        {inr(estimate.low)} – {inr(estimate.high)}
      </div>
      <div className="estimate-actions">
        <span className="estimate-muted">Suggested: <strong>{inr(estimate.point)}</strong></span>
        {onUse && <button type="button" className="link-btn" onClick={() => onUse(estimate.point)}>Use this price</button>}
        <button type="button" className="link-btn" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
          How is this calculated? {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>
      {open && (
        <ul className="estimate-factors">
          {estimate.factors.map((f) => <li key={f}>{f}</li>)}
          {estimate.comparables.count > 0 && estimate.comparables.count < 3 && (
            <li>{estimate.comparables.count} similar listing(s) on the platform ({inr(estimate.comparables.low)}
              {estimate.comparables.count > 1 ? `–${inr(estimate.comparables.high)}` : ''}): too few to use.</li>
          )}
        </ul>
      )}
      <div className="estimate-muted" style={{ fontSize: 12, marginTop: 6 }}>{estimate.disclaimer}</div>
    </div>
  );
}
