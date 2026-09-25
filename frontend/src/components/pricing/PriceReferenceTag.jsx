// Reference-price tag (Feature 2). Every reference price is shown with its
// source, when it was observed, and a status pill. Only a feed value fresher
// than the staleness window is ever labelled "Live"; admin-set values say
// "Reference · not live" and old values say "Stale".
import { inr, timeAgo, formatDateTime } from '../../utils/format';

const PILL = {
  live: 'Live',
  reference: 'Reference · not live',
  stale: 'Stale · not live',
};

export default function PriceReferenceTag({ price, compact = false }) {
  if (!price) return null;
  return (
    <div className="price-ref" title={`${price.source} — observed ${formatDateTime(price.observed_at)}`}>
      <span>Reference: <strong>{inr(price.reference_price)} / {price.unit}</strong></span>
      <span className={`price-pill ${price.status}`}>{PILL[price.status] || price.status}</span>
      {!compact && <span>{price.source} · {timeAgo(price.observed_at)}</span>}
      {compact && <span>{timeAgo(price.observed_at)}</span>}
    </div>
  );
}
