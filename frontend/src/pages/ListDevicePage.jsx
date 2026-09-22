// List a device for resale (Phase 2 → /list-device, FR-H1).
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getDevices, typeLabel } from '../services/deviceService';
import { createListing } from '../services/listingService';
import Button from '../components/ui/Button';

export default function ListDevicePage() {
  const navigate = useNavigate();
  const { data: devices } = useAsync(getDevices);
  const [form, setForm] = useState({ device_id: '', title: '', type: 'smartphone', price: '', condition: 'Good', description: '' });
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  // When a registered device is picked, prefill the title/type.
  function pickDevice(e) {
    const id = e.target.value;
    const d = devices?.find((x) => x.id === id);
    setForm((f) => ({ ...f, device_id: id, title: d ? `${d.brand} ${d.model}` : f.title, type: d ? d.type : f.type }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await createListing({ ...form, price: Number(form.price), device_id: form.device_id || null });
      toast.success('Device listed for resale');
      navigate('/marketplace');
    } catch (err) {
      toast.error(err.message);
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 560 }}>
      <Link to="/marketplace" className="back-link"><ChevronLeft size={16} /> Back to marketplace</Link>
      <h1 className="page-title">List a Device for Resale</h1>
      <p className="page-sub">Give a working device a second life by selling it.</p>

      <form className="card" onSubmit={handleSubmit}>
        <div className="field">
          <label>From my devices (optional)</label>
          <select className="select" value={form.device_id} onChange={pickDevice}>
            <option value="">— New listing —</option>
            {devices?.map((d) => <option key={d.id} value={d.id}>{d.brand} {d.model}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Title</label>
          <input className="input" value={form.title} onChange={set('title')} placeholder="e.g. Apple iPhone 12" required />
        </div>
        <div style={{ display: 'flex', gap: 14 }}>
          <div className="field" style={{ flex: 1 }}>
            <label>Type</label>
            <select className="select" value={form.type} onChange={set('type')}>
              {['smartphone', 'laptop', 'tablet'].map((t) => <option key={t} value={t}>{typeLabel(t)}</option>)}
            </select>
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>Asking price (₹)</label>
            <input className="input" type="number" min="0" value={form.price} onChange={set('price')} required />
          </div>
        </div>
        <div className="field">
          <label>Condition</label>
          <select className="select" value={form.condition} onChange={set('condition')}>
            {['Excellent', 'Good', 'Fair', 'Refurbished'].map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Description</label>
          <input className="input" value={form.description} onChange={set('description')} placeholder="Short description" />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button type="submit" disabled={busy}>{busy ? 'Listing…' : 'List Device'}</Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/marketplace')}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
