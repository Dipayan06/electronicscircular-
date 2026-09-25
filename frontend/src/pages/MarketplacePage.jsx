// Marketplace (FR-H3). Browse devices, components and recovered materials.
// "My listings" shows the seller's own items, including ones held for price
// review (Feature 4). The Materials tab shows current reference prices (Feature 2).
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAsync from '../hooks/useAsync';
import { getListings, getMyListings } from '../services/listingService';
import { getPrices } from '../services/pricingService';
import ListingCard from '../components/marketplace/ListingCard';
import PriceReferenceTag from '../components/pricing/PriceReferenceTag';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

const FILTERS = [
  ['all', 'All'], ['device', 'Devices'], ['component', 'Components'], ['material', 'Materials'], ['mine', 'My listings'],
];

export default function MarketplacePage() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('all');
  const { data, loading, error, reload } = useAsync(
    () => (filter === 'mine' ? getMyListings() : getListings(filter)), [filter]);
  const { data: prices } = useAsync(() => (filter === 'material' ? getPrices() : null), [filter]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h1 className="page-title">Marketplace</h1>
          <p className="page-sub">Buy reused devices, components and recovered materials — give them a longer life.</p>
        </div>
        <Button onClick={() => navigate('/list-device')}>+ Sell an Item</Button>
      </div>

      <div className="toolbar">
        {FILTERS.map(([val, lbl]) => (
          <button key={val} className={`chip ${filter === val ? 'active' : ''}`} onClick={() => setFilter(val)}>{lbl}</button>
        ))}
      </div>

      {filter === 'material' && prices?.items.length > 0 && (
        <div className="card" style={{ marginBottom: 18 }}>
          <strong style={{ display: 'block', marginBottom: 8 }}>Material reference prices</strong>
          <div style={{ display: 'grid', gap: 8 }}>
            {prices.items.map((p) => (
              <div key={p.material} style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
                <span style={{ fontWeight: 600, minWidth: 170 }}>{p.display_name}</span>
                <PriceReferenceTag price={p} compact />
              </div>
            ))}
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '10px 0 0' }}>
            {prices.feed_configured
              ? 'Prices marked Live come from the connected market feed; others are the last known value.'
              : 'No live market feed is connected — these are admin-managed reference values, not live market prices.'}
          </p>
        </div>
      )}

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {data && data.length === 0 && (
        <p style={{ color: 'var(--text-muted)' }}>{filter === 'mine' ? "You haven't listed anything yet." : 'No items in this category yet.'}</p>
      )}
      {data && (
        <div className="grid grid-cards">
          {data.map((l) => <ListingCard key={l.id} listing={l} />)}
        </div>
      )}
    </div>
  );
}
