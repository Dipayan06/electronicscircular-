// Admin price-review queue (Feature 4). Approve publishes the listing; reject
// marks it REJECTED. Each decision stores the reviewer, time and note (audit
// trail) and notifies the seller.
import { useState } from 'react';
import { Link } from 'react-router-dom';
import useAsync from '../../hooks/useAsync';
import { useToast } from '../../context/ToastContext';
import { getReviews, approveReview, rejectReview } from '../../services/priceReviewService';
import { inr, formatDateTime } from '../../utils/format';
import StatusBadge from '../ui/StatusBadge';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import LoadingState from '../ui/LoadingState';
import ErrorMessage from '../ui/ErrorMessage';

const STATUS_FILTERS = [['PENDING', 'Pending'], ['APPROVED', 'Approved'], ['REJECTED', 'Rejected'], ['', 'All']];

export default function PriceReviewsAdmin({ onChange }) {
  const toast = useToast();
  const [status, setStatus] = useState('PENDING');
  const { data, loading, error, reload } = useAsync(() => getReviews(status || undefined), [status]);
  const [deciding, setDeciding] = useState(null);  // { review, approve }
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);

  async function decide() {
    setBusy(true);
    try {
      const fn = deciding.approve ? approveReview : rejectReview;
      await fn(deciding.review.id, note.trim() || undefined);
      toast.success(deciding.approve ? 'Price approved — listing is live' : 'Price rejected');
      setDeciding(null);
      setNote('');
      reload();
      onChange?.();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="toolbar">
        {STATUS_FILTERS.map(([val, lbl]) => (
          <button key={lbl} className={`chip ${status === val ? 'active' : ''}`} onClick={() => setStatus(val)}>{lbl}</button>
        ))}
      </div>

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {data?.length === 0 && <p style={{ color: 'var(--text-muted)', margin: 0 }}>No reviews here.</p>}
      {data?.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Listing</th><th>Level</th><th>Price vs reference</th><th>Seller's justification</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {data.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link to={`/marketplace/${r.listing_id}`}>{r.listing_title}</Link>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{r.seller} · {formatDateTime(r.created_at)}</div>
                  </td>
                  <td><StatusBadge status={r.level} /></td>
                  <td style={{ fontSize: 13 }}>
                    {inr(r.listed_price)} / {r.listed_unit}
                    {r.reference_price != null && <> vs {inr(r.reference_price)} / {r.reference_unit}</>}
                    {r.ratio != null && <div><strong>{r.ratio}×</strong> the reference</div>}
                    {r.ratio == null && <div>{r.reason}</div>}
                  </td>
                  <td style={{ fontSize: 13, maxWidth: 240 }}>{r.justification || <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                  <td>
                    <StatusBadge status={r.status} />
                    {r.reviewer && (
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        by {r.reviewer}, {formatDateTime(r.decided_at)}{r.reviewer_note ? ` — “${r.reviewer_note}”` : ''}
                      </div>
                    )}
                  </td>
                  <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {r.status === 'PENDING' && (
                      <>
                        <Button variant="secondary" onClick={() => setDeciding({ review: r, approve: true })}>Approve</Button>{' '}
                        <Button variant="ghost" onClick={() => setDeciding({ review: r, approve: false })}>Reject</Button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={!!deciding} title={deciding?.approve ? 'Approve price' : 'Reject price'} onClose={() => setDeciding(null)}
        footer={<>
          <Button variant="secondary" onClick={() => setDeciding(null)}>Cancel</Button>
          <Button onClick={decide} disabled={busy}>{busy ? 'Saving…' : deciding?.approve ? 'Approve' : 'Reject'}</Button>
        </>}>
        <p style={{ marginTop: 0 }}>
          {deciding?.approve
            ? <>Publish <strong>{deciding?.review.listing_title}</strong> at {inr(deciding?.review.listed_price || 0)} / {deciding?.review.listed_unit}?</>
            : <>Reject the price of <strong>{deciding?.review.listing_title}</strong>? The listing will not be published.</>}
        </p>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Note to the seller (optional, kept in the audit trail)</label>
          <textarea className="input textarea" maxLength={400} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
      </Modal>
    </div>
  );
}
