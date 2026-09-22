// LifecycleTimeline — the Digital Device Passport (Phase 2 W9, FR-J). ★ signature.
// Renders events read from the database (never hardcoded — FR-J4).
const LABEL = {
  DEVICE_REGISTERED: 'Device Registered',
  CONDITION_ASSESSED: 'Condition Assessed',
  QUOTE_REQUESTED: 'Quotation Requested',
  QUOTE_ACCEPTED: 'Quotation Accepted',
  BOOKING_CONFIRMED: 'Booking Confirmed',
  REPAIR_IN_PROGRESS: 'Repair In Progress',
  REPAIR_COMPLETED: 'Repair Completed',
  LISTED_FOR_RESALE: 'Listed for Resale',
  RESERVED: 'Reserved by Buyer',
  SOLD: 'Sold',
  COLLECTION_REQUESTED: 'Collection Requested',
  COLLECTION_SCHEDULED: 'Pickup Scheduled',
  PICKED_UP: 'Picked Up',
  RECEIVED: 'Received at Facility',
  RECYCLED: 'Recycled',
};

function fmt(iso) {
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

export default function LifecycleTimeline({ events }) {
  if (!events?.length) {
    return <p style={{ color: 'var(--text-muted)' }}>No lifecycle events yet.</p>;
  }
  return (
    <div className="timeline">
      {events.map((e, i) => (
        <div className="timeline-row" key={e.id}>
          <div className="timeline-marker">
            <span className="timeline-dot" />
            {i < events.length - 1 && <span className="timeline-line" />}
          </div>
          <div className="timeline-content">
            <div style={{ fontWeight: 700 }}>{LABEL[e.type] || e.type}</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{e.description}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{fmt(e.timestamp)} · {e.actor}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
