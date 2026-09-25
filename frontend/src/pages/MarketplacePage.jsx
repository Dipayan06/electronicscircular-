// Marketplace (FR-H3). Browse devices, components and recovered materials.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAsync from '../hooks/useAsync';
import { getListings } from '../services/listingService';
import ListingCard from '../components/marketplace/ListingCard';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

const FILTERS = [
  ['all', 'All'], ['device', 'Devices'], ['component', 'Components'], ['material', 'Materials'],
];

export default function MarketplacePage() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('all');
  const { data, loading, error, reload } = useAsync(() => getListings(filter), [filter]);

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

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {data && data.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No items in this category yet.</p>}
      {data && (
        <div className="grid grid-cards">
          {data.map((l) => <ListingCard key={l.id} listing={l} />)}
        </div>
      )}
    </div>
  );
}
