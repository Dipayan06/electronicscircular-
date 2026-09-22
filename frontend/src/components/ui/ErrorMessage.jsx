// Error message (Phase 0 §14, NFR-6): friendly text, never a raw stack trace.
import { AlertTriangle } from 'lucide-react';

export default function ErrorMessage({ message = 'Something went wrong.', onRetry }) {
  return (
    <div className="card" style={{ borderColor: 'var(--status-danger)', display: 'flex', gap: 12, alignItems: 'center' }}>
      <AlertTriangle size={20} color="var(--status-danger)" />
      <span style={{ flex: 1 }}>{message}</span>
      {onRetry && <button className="btn btn-secondary" onClick={onRetry}>Retry</button>}
    </div>
  );
}
