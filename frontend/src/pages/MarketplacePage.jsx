// Marketplace (Phase 2 W7, FR-H3). Browse active + all resale listings.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAsync from '../hooks/useAsync';
import { getListings } from '../services/listingService';
import ListingCard from '../components/marketplace/ListingCard';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

const FILTERS = [['all', 'All'], ['smartphone', 'Phones'], ['laptop', 'Laptops'], ['tablet', 'Tablets']];

export default function MarketplacePage() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('all');
  const { data, loading, error, reload } = useAsync(() => getListings(filter), [filter]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h1 className="page-title">Marketplace</h1>
          <p className="page-sub">Buy reused and refurbished devices — give them a longer life.</p>
        </div>
        <Button onClick={() => navigate('/list-device')}>+ List a Device</Button>
      </div>

      <div className="toolbar">
        {FILTERS.map(([val, lbl]) => (
          <button key={val} className={`chip ${filter === val ? 'active' : ''}`} onClick={() => setFilter(val)}>{lbl}</button>
        ))}
      </div>

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {data && (
        <div className="grid grid-cards">
          {data.map((l) => <ListingCard key={l.id} listing={l} />)}
        </div>
      )}
    </div>
  );
}
