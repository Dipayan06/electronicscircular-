// Sell an Item (FR-H) — list a device, a component (RAM, GPU, CPU, motherboard,
// storage, cooler, other) or a recovered material (copper, aluminium, rare-earth,
// silicon, gold, other) sold by quantity. Route stays /list-device.
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getDevices } from '../services/deviceService';
import { createListing } from '../services/listingService';
import { KINDS, CATEGORIES, UNITS, categoryLabel } from '../config/listings.config';
import Button from '../components/ui/Button';

export default function ListDevicePage() {
  const navigate = useNavigate();
  const toast = useToast();
  const { data: devices } = useAsync(getDevices);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    kind: 'device', type: 'smartphone', device_id: '', title: '',
    price: '', condition: 'Good', description: '',
    unit: 'kg', quantity: '', min_order: '',
  });

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const isMaterial = form.kind === 'material';

  // Switching kind resets the category to that kind's first option.
  function setKind(e) {
    const kind = e.target.value;
    setForm((f) => ({ ...f, kind, type: CATEGORIES[kind][0], device_id: '' }));
  }

  // Picking a registered device prefills title (device kind only).
  function pickDevice(e) {
    const id = e.target.value;
    const d = devices?.find((x) => x.id === Number(id));
    setForm((f) => ({ ...f, device_id: id, title: d ? `${d.brand} ${d.model}` : f.title, type: d ? d.type : f.type }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    const payload = {
      kind: form.kind, type: form.type, title: form.title,
      price: Number(form.price), condition: form.condition, description: form.description,
      device_id: form.kind === 'device' && form.device_id ? Number(form.device_id) : null,
    };
    if (isMaterial) {
      payload.unit = form.unit;
      payload.quantity = Number(form.quantity);
      if (form.min_order) payload.min_order = Number(form.min_order);
    }
    try {
      await createListing(payload);
      toast.success('Item listed for sale');
      navigate('/marketplace');
    } catch (err) {
      toast.error(err.message);
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <Link to="/marketplace" className="back-link"><ChevronLeft size={16} /> Back to marketplace</Link>
      <h1 className="page-title">Sell an Item</h1>
      <p className="page-sub">List a device, a component, or recovered materials for others to buy.</p>

      <form className="card" onSubmit={handleSubmit}>
        <div className="field">
          <label>What are you selling?</label>
          <select className="select" value={form.kind} onChange={setKind}>
            {KINDS.map((k) => <option key={k.value} value={k.value}>{k.label}</option>)}
          </select>
        </div>

        {form.kind === 'device' && devices?.length > 0 && (
          <div className="field">
            <label>From my registered devices (optional)</label>
            <select className="select" value={form.device_id} onChange={pickDevice}>
              <option value="">— New listing —</option>
              {devices.map((d) => <option key={d.id} value={d.id}>{d.brand} {d.model}</option>)}
            </select>
          </div>
        )}

        <div className="field">
          <label>Category</label>
          <select className="select" value={form.type} onChange={set('type')}>
            {CATEGORIES[form.kind].map((c) => <option key={c} value={c}>{categoryLabel(c)}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Title</label>
          <input className="input" value={form.title} onChange={set('title')}
                 placeholder={isMaterial ? 'e.g. Recovered copper from cabling' : 'e.g. NVIDIA RTX 3060'} required />
        </div>

        {!isMaterial ? (
          <div className="field">
            <label>Price (₹)</label>
            <input className="input" type="number" min="1" value={form.price} onChange={set('price')} required />
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: 14 }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Price per unit (₹)</label>
                <input className="input" type="number" min="0" step="any" value={form.price} onChange={set('price')} required />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Unit</label>
                <select className="select" value={form.unit} onChange={set('unit')}>
                  {UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 14 }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Quantity available</label>
                <input className="input" type="number" min="0" step="any" value={form.quantity} onChange={set('quantity')} required />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Minimum order (optional)</label>
                <input className="input" type="number" min="0" step="any" value={form.min_order} onChange={set('min_order')} placeholder="e.g. 5" />
              </div>
            </div>
          </>
        )}

        <div className="field">
          <label>Condition</label>
          <select className="select" value={form.condition} onChange={set('condition')}>
            {(isMaterial ? ['Recovered', 'Refined'] : ['Excellent', 'Good', 'Fair', 'Refurbished', 'For parts']).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Description</label>
          <input className="input" value={form.description} onChange={set('description')} placeholder="Short description" />
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <Button type="submit" disabled={busy}>{busy ? 'Listing…' : 'List for Sale'}</Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/marketplace')}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
