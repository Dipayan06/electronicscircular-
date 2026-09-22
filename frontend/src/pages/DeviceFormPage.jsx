// Register a device (Phase 2 W3 → new, FR-B1/B2).
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { createDevice, DEVICE_TYPES, typeLabel } from '../services/deviceService';
import Button from '../components/ui/Button';

const WORKING = [
  ['working', 'Working'],
  ['faulty', 'Faulty'],
  ['not_working', 'Not working'],
];

export default function DeviceFormPage() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({
    type: 'smartphone', brand: '', model: '', serial: '',
    purchase_year: new Date().getFullYear() - 1,
    working_status: 'working', accessories: '',
  });

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const device = await createDevice({ ...form, purchase_year: Number(form.purchase_year) });
      navigate(`/devices/${device.id}`);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <div style={{ maxWidth: 620 }}>
      <Link to="/devices" className="back-link"><ChevronLeft size={16} /> Back to devices</Link>
      <h1 className="page-title">Register a Device</h1>
      <p className="page-sub">Add a smartphone, laptop or tablet to track its lifecycle.</p>

      <form className="card" onSubmit={handleSubmit}>
        <div className="field">
          <label>Device type</label>
          <select className="select" value={form.type} onChange={set('type')}>
            {DEVICE_TYPES.map((t) => <option key={t} value={t}>{typeLabel(t)}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', gap: 14 }}>
          <div className="field" style={{ flex: 1 }}>
            <label>Brand</label>
            <input className="input" value={form.brand} onChange={set('brand')} placeholder="e.g. Dell" required />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>Model</label>
            <input className="input" value={form.model} onChange={set('model')} placeholder="e.g. XPS 13" required />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 14 }}>
          <div className="field" style={{ flex: 1 }}>
            <label>Serial / IMEI</label>
            <input className="input" value={form.serial} onChange={set('serial')} placeholder="Optional" />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>Purchase year</label>
            <input className="input" type="number" min="2005" max={new Date().getFullYear()} value={form.purchase_year} onChange={set('purchase_year')} required />
          </div>
        </div>

        <div className="field">
          <label>Working status</label>
          <select className="select" value={form.working_status} onChange={set('working_status')}>
            {WORKING.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Accessories (optional)</label>
          <input className="input" value={form.accessories} onChange={set('accessories')} placeholder="e.g. Charger, Case" />
        </div>

        {error && <p style={{ color: 'var(--status-danger)', fontSize: 14 }}>{error}</p>}

        <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
          <Button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Register Device'}</Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/devices')}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
