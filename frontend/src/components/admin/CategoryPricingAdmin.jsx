// Admin: typical new prices + depreciation per device/component category. These
// anchor the resale estimate only when a seller doesn't say what they paid.
import { useState } from 'react';
import useAsync from '../../hooks/useAsync';
import { useToast } from '../../context/ToastContext';
import { getCategoryPrices, updateCategoryPrice } from '../../services/valuationService';
import { inr, timeAgo } from '../../utils/format';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import LoadingState from '../ui/LoadingState';
import ErrorMessage from '../ui/ErrorMessage';

export default function CategoryPricingAdmin() {
  const toast = useToast();
  const { data, loading, error, reload } = useAsync(getCategoryPrices);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  function edit(c) {
    setEditing(c);
    setForm({
      typical_new_price: c.typical_new_price, source_note: '',
      annual_depreciation: Math.round(c.annual_depreciation * 100),
      residual_floor: Math.round(c.residual_floor * 100),
    });
  }

  async function save() {
    setBusy(true);
    try {
      const payload = {
        annual_depreciation: Number(form.annual_depreciation) / 100,
        residual_floor: Number(form.residual_floor) / 100,
      };
      // Only send the price when it changed, so its timestamp stays meaningful.
      if (Number(form.typical_new_price) !== editing.typical_new_price) {
        payload.typical_new_price = Number(form.typical_new_price);
        if (form.source_note.trim()) payload.source_note = form.source_note.trim();
      }
      await updateCategoryPrice(editing.category, payload);
      toast.success(`${editing.display_name} updated`);
      setEditing(null);
      reload();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;

  return (
    <div>
      <p style={{ margin: '0 0 12px', fontSize: 13, color: 'var(--text-muted)' }}>
        Used for resale estimates only when the seller doesn't enter what they paid. These are admin
        references, not market data. Sellers are told when an estimate relies on them.
      </p>
      <div className="table-wrap">
        <table className="table">
          <thead><tr><th>Category</th><th>Typical new price</th><th>Loses / year</th><th>Min value</th><th>Source</th><th></th></tr></thead>
          <tbody>
            {data.map((c) => (
              <tr key={c.category}>
                <td><strong>{c.display_name}</strong><div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{c.kind}</div></td>
                <td>{inr(c.typical_new_price)}</td>
                <td>{Math.round(c.annual_depreciation * 100)}%</td>
                <td>{Math.round(c.residual_floor * 100)}%</td>
                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{c.source} · {timeAgo(c.observed_at)}</td>
                <td style={{ textAlign: 'right' }}><Button variant="secondary" onClick={() => edit(c)}>Edit</Button></td>
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
        <div className="field">
          <label>Typical new price (₹)</label>
          <input className="input" type="number" min="1" value={form.typical_new_price ?? ''} onChange={set('typical_new_price')} />
        </div>
        <div className="field">
          <label>Source note (where this value came from)</label>
          <input className="input" maxLength={120} value={form.source_note ?? ''} onChange={set('source_note')}
                 placeholder="e.g. Average of 3 retailers, Sep 2026" />
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <div className="field" style={{ flex: 1 }}>
            <label>Loses per year (%)</label>
            <input className="input" type="number" min="0" max="99" value={form.annual_depreciation ?? ''} onChange={set('annual_depreciation')} />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>Never below (% of price)</label>
            <input className="input" type="number" min="0" max="100" value={form.residual_floor ?? ''} onChange={set('residual_floor')} />
          </div>
        </div>
      </Modal>
    </div>
  );
}
