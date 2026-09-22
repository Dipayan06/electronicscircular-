// Empty state (Phase 0 §14, Phase 2 §2.7): shown when a list has no data.
import { Inbox } from 'lucide-react';

export default function EmptyState({ title = 'Nothing here yet', hint, action }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
      <Inbox size={30} color="var(--text-muted)" />
      <p style={{ fontWeight: 700, margin: '10px 0 4px' }}>{title}</p>
      {hint && <p style={{ color: 'var(--text-muted)', fontSize: 14, margin: '0 0 14px' }}>{hint}</p>}
      {action}
    </div>
  );
}
