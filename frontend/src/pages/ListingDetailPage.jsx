// Listing detail + simulated purchase (FR-H4). Materials let the buyer choose a
// quantity (buy in appropriate amounts or in bulk); no real payment is taken.
import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getListing, reserveListing } from '../services/listingService';
import { getPrices } from '../services/pricingService';
import { getMyReviews } from '../services/priceReviewService';
import { useAuth } from '../context/AuthContext';
import { categoryLabel, kindLabel } from '../config/listings.config';
import PriceReferenceTag from '../components/pricing/PriceReferenceTag';
import ListingGallery from '../components/marketplace/ListingGallery';

// Feature 4: what buyers/sellers see for listings held by price regulation.
const REVIEW_NOTE = {
  PRICE_REVIEW_REQUIRED: 'The price of this item is being reviewed by an admin. It can be bought once approved.',
  SUSPENDED_PENDING_REVIEW: 'This listing is held for price review and is not visible to buyers yet.',
  REJECTED: 'An admin rejected the price of this listing.',
};
import StatusBadge from '../components/ui/StatusBadge';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

export default function ListingDetailPage() {
  const { id } = useParams();
  const toast = useToast();
  const { data, loading, error, reload, setData } = useAsync(() => getListing(id), [id]);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [qty, setQty] = useState('');

  const { user } = useAuth();
  const isMaterial = data?.kind === 'material';
  const isOwner = data && user && data.seller_id === user.id;
  const { data: prices } = useAsync(() => (isMaterial ? getPrices() : null), [isMaterial]);
  const reference = prices?.items.find((p) => p.material === data?.type);
  const underReview = data && REVIEW_NOTE[data.status];
  const { data: myReviews } = useAsync(() => (isOwner && underReview ? getMyReviews() : null), [isOwner, underReview]);
  const review = myReviews?.find((r) => r.listing_id === data?.id);

  function openBuy() {
    if (isMaterial) setQty(String(data.min_order || 1));
    setConfirm(true);
  }

  async function buy() {
    setBusy(true);
    try {
      await reserveListing(id, isMaterial ? Number(qty) : undefined);
      toast.success(isMaterial ? 'Purchase confirmed' : 'Listing reserved');
      setConfirm(false);
      reload();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;

  const total = isMaterial && qty ? Number(qty) * data.price : null;

  return (
    <div style={{ maxWidth: 560 }}>
      <Link to="/marketplace" className="back-link"><ChevronLeft size={16} /> Back to marketplace</Link>
      <h1 className="page-title">{data.title}</h1>
      <div style={{ fontSize: 30, fontWeight: 800, color: 'var(--green-dark)', marginBottom: 12 }}>
        ₹{data.price.toLocaleString('en-IN')}{isMaterial ? <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-muted)' }}> / {data.unit}</span> : null}
      </div>
      {reference && <div style={{ marginBottom: 14 }}><PriceReferenceTag price={reference} /></div>}

      {underReview && (
        <div className={`price-check ${data.status === 'PRICE_REVIEW_REQUIRED' ? 'REVIEW' : 'EXTREME'}`} style={{ margin: '0 0 14px' }}>
          <strong>{data.status.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase())}</strong>
          {REVIEW_NOTE[data.status]}
          {review && (
            <div style={{ marginTop: 6 }}>
              Reason: {review.reason}
              {review.justification && <><br />Your justification: {review.justification}</>}
              {review.reviewer_note && <><br />Admin note: {review.reviewer_note}</>}
            </div>
          )}
        </div>
      )}

      <ListingGallery listing={data} isOwner={isOwner} onChange={setData} />

      <div className="card">
        <dl className="kv">
          <dt>Type</dt><dd>{kindLabel(data.kind)} · {categoryLabel(data.type)}</dd>
          {isMaterial && <><dt>Available</dt><dd>{data.quantity?.toLocaleString('en-IN')} {data.unit}{data.min_order ? ` (min order ${data.min_order} ${data.unit})` : ''}</dd></>}
          <dt>Condition</dt><dd>{data.condition || '—'}</dd>
          <dt>Seller</dt><dd>{data.seller}</dd>
          <dt>Status</dt><dd><StatusBadge status={data.status} /></dd>
          <dt>Description</dt><dd>{data.description || '—'}</dd>
        </dl>
        <div style={{ marginTop: 18 }}>
          {data.status === 'ACTIVE' && <Button onClick={openBuy}>{isMaterial ? 'Buy quantity' : 'Reserve this item'}</Button>}
          {data.status !== 'ACTIVE' && (!underReview || data.status === 'REJECTED') && (
            <p style={{ color: 'var(--text-muted)', margin: 0 }}>This item is {data.status.toLowerCase()} and no longer available.</p>
          )}
          {underReview && data.status !== 'REJECTED' && <p style={{ color: 'var(--text-muted)', margin: 0 }}>Not available to buy while the price is under review.</p>}
        </div>
        <div className="placeholder-note" style={{ marginTop: 14 }}>
          Simulated purchase — payment integration is out of scope for the prototype.
        </div>
      </div>

      <Modal open={confirm} title={isMaterial ? 'Buy material' : 'Confirm reservation'} onClose={() => setConfirm(false)}
        footer={<>
          <Button variant="secondary" onClick={() => setConfirm(false)}>Cancel</Button>
          <Button onClick={buy} disabled={busy || (isMaterial && !qty)}>{busy ? 'Processing…' : 'Confirm'}</Button>
        </>}>
        {isMaterial ? (
          <>
            <div className="field">
              <label>Quantity ({data.unit}) — available {data.quantity?.toLocaleString('en-IN')}{data.min_order ? `, min ${data.min_order}` : ''}</label>
              <input className="input" type="number" min={data.min_order || 0} max={data.quantity} step="any"
                     value={qty} onChange={(e) => setQty(e.target.value)} />
            </div>
            <p style={{ margin: 0 }}>
              Total: <strong>₹{(total || 0).toLocaleString('en-IN')}</strong> for {qty || 0} {data.unit} @ ₹{data.price.toLocaleString('en-IN')}/{data.unit}.
              {' '}(No payment is taken in this prototype.)
            </p>
          </>
        ) : (
          <p style={{ margin: 0 }}>Reserve <strong>{data.title}</strong> for ₹{data.price.toLocaleString('en-IN')}? (No payment is taken in this prototype.)</p>
        )}
      </Modal>
    </div>
  );
}
