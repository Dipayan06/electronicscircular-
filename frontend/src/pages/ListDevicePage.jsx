// Sell an Item (FR-H) — list a device, a component (RAM, GPU, CPU, motherboard,
// storage, cooler, other) or a recovered material (copper, aluminium, rare-earth,
// silicon, gold, other) sold by quantity. Route stays /list-device.
import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getDevices } from '../services/deviceService';
import { createListing } from '../services/listingService';
import { getPrices, checkPrice } from '../services/pricingService';
import { KINDS, CATEGORIES, UNITS, categoryLabel } from '../config/listings.config';
import Button from '../components/ui/Button';
import PriceReferenceTag from '../components/pricing/PriceReferenceTag';
import EstimateCard from '../components/pricing/EstimateCard';
import { getEstimate } from '../services/valuationService';
import { draftListing } from '../services/assistantService';

const THIS_YEAR = new Date().getFullYear();

const LEVEL_TITLE = {
  NORMAL: 'Price looks fair',
  REVIEW: 'Price needs review',
  EXTREME: 'Price is far above the reference',
};

export default function ListDevicePage() {
  const navigate = useNavigate();
  const toast = useToast();
  const { data: devices } = useAsync(getDevices);
  const { data: prices } = useAsync(getPrices);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    kind: 'device', type: 'smartphone', device_id: '', title: '',
    price: '', condition: 'Good', description: '',
    unit: 'kg', quantity: '', min_order: '', price_justification: '',
    purchase_price: '', purchase_year: '',
  });
  const [check, setCheck] = useState(null);
  const [estimate, setEstimate] = useState(null);
  const [estimating, setEstimating] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [draftNote, setDraftNote] = useState('');

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const isMaterial = form.kind === 'material';
  const reference = isMaterial ? prices?.items.find((p) => p.material === form.type) : null;

  // Feature 4: preview the price band as the seller types (debounced). This is
  // advisory — the server repeats the check when the listing is submitted.
  useEffect(() => {
    const price = Number(form.price);
    if (!isMaterial || !(price > 0)) { setCheck(null); return undefined; }
    const t = setTimeout(() => {
      checkPrice({ kind: form.kind, type: form.type, unit: form.unit, price })
        .then(setCheck)
        .catch(() => setCheck(null));
    }, 350);
    return () => clearTimeout(t);
  }, [isMaterial, form.kind, form.type, form.unit, form.price]);

  const needsJustification = check?.level === 'REVIEW';

  // Resale estimate for devices/components, refreshed as the details change.
  // The purchase price/year are only used for the estimate, not stored.
  useEffect(() => {
    if (isMaterial) { setEstimate(null); return undefined; }
    const payload = { kind: form.kind, type: form.type, condition: form.condition };
    if (form.device_id) payload.device_id = Number(form.device_id);
    if (Number(form.purchase_price) > 0) payload.purchase_price = Number(form.purchase_price);
    const year = Number(form.purchase_year);
    if (year >= 1990 && year <= THIS_YEAR) payload.purchase_year = year;
    setEstimating(true);
    const t = setTimeout(() => {
      getEstimate(payload)
        .then(setEstimate)
        .catch(() => setEstimate(null))
        .finally(() => setEstimating(false));
    }, 400);
    return () => clearTimeout(t);
  }, [isMaterial, form.kind, form.type, form.condition, form.device_id, form.purchase_price, form.purchase_year]);

  // Switching kind resets the category to that kind's first option.
  function setKind(e) {
    const kind = e.target.value;
    setForm((f) => ({ ...f, kind, type: CATEGORIES[kind][0], device_id: '', purchase_price: '', purchase_year: '' }));
  }

  // Picking a registered device prefills title (device kind only).
  function pickDevice(e) {
    const id = e.target.value;
    const d = devices?.find((x) => x.id === Number(id));
    setForm((f) => ({
      ...f, device_id: id, title: d ? `${d.brand} ${d.model}` : f.title, type: d ? d.type : f.type,
      purchase_year: d?.purchase_year ? String(d.purchase_year) : f.purchase_year,
    }));
  }

  // The assistant drafts a title + description from the device's assessment.
  // The seller can edit both before listing.
  async function writeForMe() {
    setDrafting(true);
    try {
      const d = await draftListing(form.device_id);
      setForm((f) => ({ ...f, title: d.title, description: d.description }));
      setDraftNote(d.source === 'model'
        ? 'Written by the assistant from your condition assessment. Edit anything before listing.'
        : 'Basic draft from your device details. Edit anything before listing.');
    } catch (err) {
      setDraftNote(err.message);
    } finally {
      setDrafting(false);
    }
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
      if (form.price_justification.trim()) payload.price_justification = form.price_justification.trim();
    }
    try {
      const listing = await createListing(payload);
      if (listing.status === 'ACTIVE') {
        toast.success('Item listed for sale');
        navigate('/marketplace');
      } else {
        // Held for price review — show the seller their listing and its status.
        toast.info(listing.status === 'SUSPENDED_PENDING_REVIEW'
          ? 'Listing held: an admin must review the price before it is published.'
          : 'Listed, but the price is under review — buyers can’t purchase it until approved.');
        navigate(`/marketplace/${listing.id}`);
      }
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
          <>
            <div style={{ display: 'flex', gap: 14 }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Price paid ₹ (optional)</label>
                <input className="input" type="number" min="1" value={form.purchase_price} onChange={set('purchase_price')}
                       placeholder="e.g. 45000" title="What you paid when new, improves the estimate" />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Year bought (optional)</label>
                <input className="input" type="number" min="1990" max={THIS_YEAR} value={form.purchase_year}
                       onChange={set('purchase_year')} placeholder={String(THIS_YEAR - 2)} />
              </div>
            </div>
            <EstimateCard estimate={estimate} loading={estimating}
                          onUse={(p) => setForm((f) => ({ ...f, price: String(p) }))} />
            <div className="field">
              <label>Price (₹)</label>
              <input className="input" type="number" min="1" value={form.price} onChange={set('price')} required />
            </div>
          </>
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
            {reference && <div style={{ margin: '-6px 0 12px' }}><PriceReferenceTag price={reference} /></div>}
            {check?.regulated && (
              <div className={`price-check ${check.level}`} role="status">
                <strong>{LEVEL_TITLE[check.level]}</strong>
                {check.reason}
              </div>
            )}
            {check && !check.regulated && (
              <div className="price-check muted" role="status">{check.reason}</div>
            )}
            {(needsJustification || check?.level === 'EXTREME') && (
              <div className="field">
                <label>Why is this price different? {needsJustification ? '(required)' : '(optional, helps the admin)'}</label>
                <textarea className="input textarea" value={form.price_justification} onChange={set('price_justification')}
                          minLength={needsJustification ? 10 : undefined} maxLength={600} required={needsJustification}
                          placeholder="e.g. Audio-grade oxygen-free copper, certified purity" />
              </div>
            )}
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
          <label htmlFor="description">Description</label>
          <textarea id="description" className="input textarea" value={form.description} onChange={set('description')}
                    placeholder="Short description" />
          {form.kind === 'device' && form.device_id && (
            <div className="assist-row">
              <Button type="button" variant="secondary" onClick={writeForMe} disabled={drafting}>
                {drafting ? 'Writing…' : 'Write title & description for me'}
              </Button>
              {draftNote && <span className="assist-note" role="status">{draftNote}</span>}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <Button type="submit" disabled={busy}>{busy ? 'Listing…' : 'List for Sale'}</Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/marketplace')}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
