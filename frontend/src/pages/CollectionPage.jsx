// Collection & recycling (Phase 2 W8, FR-I). Request a pickup and track it
// through REQUESTED → SCHEDULED → PICKED_UP → RECEIVED → RECYCLED. The collector
// action (advance) is exposed as a demo control to show the full flow.
import { useState } from 'react';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getDevices } from '../services/deviceService';
import { getProviders } from '../services/providerService';
import { getCollections, requestCollection, advanceCollection, COLLECTION_FLOW } from '../services/collectionService';
import StatusStepper from '../components/ui/StatusStepper';
import StatusBadge from '../components/ui/StatusBadge';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

export default function CollectionPage() {
  const { data: devices } = useAsync(getDevices);
  const { data: collectors } = useAsync(() => getProviders('recycler'));
  const { data: collections, loading, error, reload } = useAsync(getCollections);

  const [form, setForm] = useState({ device_id: '', collector_id: '', address: '', preferred_date: '' });
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await requestCollection({
        device_id: form.device_id || devices?.[0]?.id,
        collector_id: form.collector_id || collectors?.[0]?.id,
        address: form.address, preferred_date: form.preferred_date,
      });
      toast.success('Collection requested');
      setForm({ device_id: '', collector_id: '', address: '', preferred_date: '' });
      reload();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function advance(c) {
    const next = COLLECTION_FLOW[COLLECTION_FLOW.indexOf(c.status) + 1];
    if (!next) return;
    try {
      await advanceCollection(c.id, next);
      reload();
    } catch (err) {
      toast.error(err.message);
    }
  }

  return (
    <div style={{ maxWidth: 780 }}>
      <h1 className="page-title">Collection &amp; Recycling</h1>
      <p className="page-sub">Request a pickup for end-of-life devices and track recycling.</p>

      <form className="card" onSubmit={submit} style={{ marginBottom: 22 }}>
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>Device</label>
            <select className="select" value={form.device_id} onChange={set('device_id')} required>
              <option value="">Select a device</option>
              {devices?.map((d) => <option key={d.id} value={d.id}>{d.brand} {d.model}</option>)}
            </select>
          </div>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>Collector</label>
            <select className="select" value={form.collector_id} onChange={set('collector_id')} required>
              <option value="">Select a collector</option>
              {collectors?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          <div className="field" style={{ flex: 2, minWidth: 200 }}>
            <label>Pickup address</label>
            <input className="input" value={form.address} onChange={set('address')} placeholder="Address" required />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 150 }}>
            <label>Preferred date</label>
            <input className="input" type="date" value={form.preferred_date} onChange={set('preferred_date')} required />
          </div>
        </div>
        <Button type="submit" disabled={busy}>{busy ? 'Requesting…' : 'Request Pickup'}</Button>
      </form>

      <h2 style={{ fontSize: 17, marginBottom: 10 }}>Active collections</h2>
      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {collections && collections.length === 0 && (
        <p style={{ color: 'var(--text-muted)' }}>No collection requests yet.</p>
      )}
      {collections && collections.map((c) => {
        const done = c.status === 'RECYCLED';
        return (
          <div className="card" key={c.id} style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <strong style={{ flex: 1 }}>{c.device?.brand} {c.device?.model} · {c.collector?.name}</strong>
              <StatusBadge status={c.status} />
            </div>
            <StatusStepper steps={COLLECTION_FLOW} current={c.status} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 30 }}>
              {!done && <Button variant="ghost" onClick={() => advance(c)}>Advance status (collector)</Button>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
