// Status badge (Phase 0 §14). One component renders every lifecycle status
// with the colour map from Phase 2 §2.1. Add new statuses here only.

const TONE = {
  // pending / waiting
  PENDING: 'pending', REQUESTED: 'pending', SENT: 'pending',
  // in progress
  IN_PROGRESS: 'progress', CONFIRMED: 'progress', SCHEDULED: 'progress',
  PICKED_UP: 'progress', RESERVED: 'progress', RECEIVED: 'progress',
  // success / active
  ACCEPTED: 'success', COMPLETED: 'success', ACTIVE: 'success',
  RECYCLED: 'success', VERIFIED: 'success', SOLD: 'success',
  // danger
  REJECTED: 'danger', CANCELLED: 'danger', EXPIRED: 'danger',
  // price regulation (Feature 4)
  PRICE_REVIEW_REQUIRED: 'pending', SUSPENDED_PENDING_REVIEW: 'danger', APPROVED: 'success',
  NORMAL: 'success', REVIEW: 'pending', EXTREME: 'danger',
  // neutral
  REMOVED: 'neutral', CLOSED: 'neutral',
  // device working status
  WORKING: 'success', FAULTY: 'pending', NOT_WORKING: 'danger',
};

const COLORS = {
  pending:  ['var(--status-pending)',  'var(--status-pending-bg)'],
  progress: ['var(--status-progress)', 'var(--status-progress-bg)'],
  success:  ['var(--status-success)',  'var(--status-success-bg)'],
  danger:   ['var(--status-danger)',   'var(--status-danger-bg)'],
  neutral:  ['var(--status-neutral)',  'var(--status-neutral-bg)'],
};

export default function StatusBadge({ status }) {
  const tone = TONE[status] || 'neutral';
  const [color, bg] = COLORS[tone];
  return (
    <span className="badge" style={{ color, background: bg }}>
      {String(status).replace(/_/g, ' ')}
    </span>
  );
}
