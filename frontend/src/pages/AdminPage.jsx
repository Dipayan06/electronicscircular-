// Admin dashboard (Phase 2 W10, FR-K2/K3). Overview stats + management tables.
// The Providers tab lets an admin verify a pending provider (FR-K3).
import { useState } from 'react';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getProviders, verifyProvider, providerTypeLabel } from '../services/providerService';
import { getDevices, typeLabel } from '../services/deviceService';
import { getListings } from '../services/listingService';
import StatCard from '../components/ui/StatCard';
import StatusBadge from '../components/ui/StatusBadge';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import PricingAdmin from '../components/admin/PricingAdmin';
import PriceReviewsAdmin from '../components/admin/PriceReviewsAdmin';
import { getReviews } from '../services/priceReviewService';

const TABS = [
  ['providers', 'Providers'], ['devices', 'Devices'], ['listings', 'Listings'],
  ['reviews', 'Price reviews'], ['pricing', 'Material pricing'],
];

export default function AdminPage() {
  const [tab, setTab] = useState('providers');
  const { data: providers, loading: lp, reload: reloadProviders } = useAsync(() => getProviders('all'));
  const { data: devices, loading: ld } = useAsync(getDevices);
  const { data: listings, reload: reloadListings } = useAsync(() => getListings('all'));
  const { data: pendingReviews, reload: reloadReviews } = useAsync(() => getReviews('PENDING'));

  const toast = useToast();
  async function verify(id) {
    try { await verifyProvider(id); toast.success('Provider verified'); reloadProviders(); }
    catch (err) { toast.error(err.message); }
  }

  const pending = providers?.filter((p) => !p.verified).length || 0;
  const stats = [
    { value: providers?.length ?? '—', label: 'Providers', icon: 'Wrench' },
    { value: devices?.length ?? '—', label: 'Devices', icon: 'Smartphone' },
    { value: providers?.filter((p) => p.verified).length ?? '—', label: 'Verified', icon: 'BadgeCheck' },
    { value: pending, label: 'Pending Verif.', icon: 'Clock' },
    { value: listings?.filter((l) => l.status === 'ACTIVE').length ?? '—', label: 'Listings', icon: 'Store' },
    { value: pendingReviews?.length ?? '—', label: 'Price Reviews', icon: 'Scale' },
  ];

  return (
    <div>
      <h1 className="page-title">Admin Overview</h1>
      <p className="page-sub">Oversee providers, devices and marketplace activity.</p>

      <div className="grid grid-stats" style={{ marginBottom: 22 }}>
        {stats.map((s) => <StatCard key={s.label} {...s} />)}
      </div>

      <div className="tabs">
        {TABS.map(([t, label]) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {label}{t === 'reviews' && pendingReviews?.length ? ` (${pendingReviews.length})` : ''}
          </button>
        ))}
      </div>

      <div className="card">
        {tab === 'providers' && (lp ? <LoadingState /> : (
          <table className="table">
            <thead><tr><th>Provider</th><th>Type</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {providers.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{providerTypeLabel(p.type)}</td>
                  <td><StatusBadge status={p.verified ? 'VERIFIED' : 'PENDING'} /></td>
                  <td style={{ textAlign: 'right' }}>{!p.verified && <Button variant="secondary" onClick={() => verify(p.id)}>Verify</Button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}

        {tab === 'devices' && (ld ? <LoadingState /> : (
          <table className="table">
            <thead><tr><th>Device</th><th>Type</th><th>Year</th><th>Recommendation</th></tr></thead>
            <tbody>
              {devices.map((d) => (
                <tr key={d.id}>
                  <td>{d.brand} {d.model}</td>
                  <td>{typeLabel(d.type)}</td>
                  <td>{d.purchase_year}</td>
                  <td>{d.recommendation ? <StatusBadge status={d.recommendation} /> : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}

        {tab === 'listings' && (
          <table className="table">
            <thead><tr><th>Listing</th><th>Price</th><th>Seller</th><th>Status</th></tr></thead>
            <tbody>
              {listings?.map((l) => (
                <tr key={l.id}>
                  <td>{l.title}</td>
                  <td>₹{l.price.toLocaleString('en-IN')}</td>
                  <td>{l.seller}</td>
                  <td><StatusBadge status={l.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {tab === 'reviews' && <PriceReviewsAdmin onChange={() => { reloadReviews(); reloadListings(); }} />}
        {tab === 'pricing' && <PricingAdmin />}
      </div>
    </div>
  );
}
