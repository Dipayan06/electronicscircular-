// Admin pricing panel (Features 2 + 4). Set each material's reference price and
// its regulation band. Admin-entered values are always labelled "reference"
// (never live). If a market feed is configured, "Refresh from feed" pulls it;
// failures keep the last-known value and are shown per material.
import { useState } from 'react';
import useAsync from '../../hooks/useAsync';
import { useToast } from '../../context/ToastContext';
import { getPrices, setPrice, refreshFromFeed, getPriceHistory } from '../../services/pricingService';
import { inr, formatDateTime } from '../../utils/format';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import LoadingState from '../ui/LoadingState';
import ErrorMessage from '../ui/ErrorMessage';
import PriceReferenceTag from '../pricing/PriceReferenceTag';

const MASS_UNITS = ['g', 'kg', 'tonne'];

export default function PricingAdmin() {
  const toast = useToast();
  const { data, loading, error, reload } = useAsync(getPrices);
  const [editing, setEditing] = useState(null);   // material row being edited
  const [form, setForm] = useState({});
  const [history, setHistory] = useState(null);
  const [busy, setBusy] = useState(false);

  function edit(p) {
    setEditing(p);
    setForm({
      reference_price: p.reference_price, unit: p.unit, source_note: '',
      band_min: p.band_min, band_max: p.band_max, extreme_max: p.extreme_max,
    });
  }
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function save() {
    setBusy(true);
    try {
      const payload = {
        band_min: Number(form.band_min), band_max: Number(form.band_max), extreme_max: Number(form.extreme_max),
      };
      // Only send the price if it changed, so a band tweak doesn't reset the price's timestamp.
      if (Number(form.reference_price) !== editing.reference_price || form.unit !== editing.unit) {
        payload.reference_price = Number(form.reference_price);
        payload.unit = form.unit;
        if (form.source_note.trim()) payload.source_note = form.source_note.trim();
      }
      await setPrice(editing.material, payload);
      toast.success(`${editing.display_name} updated`);
      setEditing(null);
      reload();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function refresh() {
    try {
      const res = await refreshFromFeed();
      const failed = Object.values(res).filter((v) => v !== 'updated').length;
      failed ? toast.error(`${failed} material(s) failed — last-known values kept`) : toast.success('Prices refreshed from feed');
      reload();
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function showHistory(p) {
    try {
      setHistory({ material: p, rows: await getPriceHistory(p.material) });
    } catch (err) {
      toast.error(err.message);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)', maxWidth: 520 }}>
          {data.feed_configured
            ? 'A market-data feed is configured. Refresh to pull current prices; failures keep the last-known value.'
            : 'No market feed configured (PRICE_API_BASE_URL). Values below are admin-managed references and are shown to users as "not live".'}
        </p>
        <Button variant="secondary" onClick={refresh} disabled={!data.feed_configured}>Refresh from feed</Button>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead><tr><th>Material</th><th>Reference</th><th>Band (NORMAL / EXTREME)</th><th>Updated</th><th></th></tr></thead>
          <tbody>
            {data.items.map((p) => (
              <tr key={p.material}>
                <td><strong>{p.display_name}</strong></td>
                <td>
                  <PriceReferenceTag price={p} compact />
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{p.source}</div>
                  {p.last_fetch_error && <div style={{ fontSize: 12, color: 'var(--status-danger)' }}>Feed error: {p.last_fetch_error}</div>}
                </td>
                <td style={{ whiteSpace: 'nowrap' }}>{p.band_min}×–{p.band_max}× / &gt;{p.extreme_max}×</td>
                <td style={{ fontSize: 13 }}>{formatDateTime(p.updated_at)}</td>
                <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <Button variant="ghost" onClick={() => showHistory(p)}>History</Button>
                  <Button variant="secondary" onClick={() => edit(p)}>Edit</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal open={!!editing} title={`Edit ${editing?.display_name || ''}`} onClose={() => setEditing(null)}
        footer={<>
          <Button variant="secondary" onClick={() => setEditing(null)}>Cancel</Button>
          <Button onClick={save} disabled={busy}>{busy ? 'Saving…' : 'Save'}</Button>
        </>}>
        <div style={{ display: 'flex', gap: 12 }}>
          <div className="field" style={{ flex: 2 }}>
            <label>Reference price (₹)</label>
            <input className="input" type="number" min="0" step="any" value={form.reference_price ?? ''} onChange={set('reference_price')} />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>Per</label>
            <select className="select" value={form.unit} onChange={set('unit')}>
              {MASS_UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>
        </div>
        <div className="field">
          <label>Source note (where this value came from)</label>
          <input className="input" maxLength={120} value={form.source_note ?? ''} onChange={set('source_note')}
                 placeholder="e.g. MCX close 25 Sep, dealer quote" />
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <div className="field" style={{ flex: 1 }}>
            <label>Normal min ×</label>
            <input className="input" type="number" min="0" step="0.05" value={form.band_min ?? ''} onChange={set('band_min')} />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>Normal max ×</label>
            <input className="input" type="number" min="1" step="0.05" value={form.band_max ?? ''} onChange={set('band_max')} />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>Extreme above ×</label>
            <input className="input" type="number" min="1" step="0.1" value={form.extreme_max ?? ''} onChange={set('extreme_max')} />
          </div>
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
          Between min and max → auto-approved. Below min, or between max and extreme → admin review with justification.
          Above extreme → listing hidden until reviewed.
        </p>
      </Modal>

      <Modal open={!!history} title={`${history?.material.display_name || ''} — price history`} onClose={() => setHistory(null)}
        footer={<Button variant="secondary" onClick={() => setHistory(null)}>Close</Button>}>
        {history?.rows.length === 0 && <p style={{ margin: 0 }}>No history yet.</p>}
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Price</th><th>Source</th><th>Recorded</th></tr></thead>
            <tbody>
              {history?.rows.map((h, i) => (
                <tr key={i}>
                  <td style={{ whiteSpace: 'nowrap' }}>{inr(h.reference_price)} / {h.unit}</td>
                  <td style={{ fontSize: 13 }}>{h.source}</td>
                  <td style={{ fontSize: 13 }}>{formatDateTime(h.recorded_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Modal>
    </div>
  );
}
