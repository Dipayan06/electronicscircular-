// Provider directory (Phase 2 W5, FR-E) with type filter + quote-request modal.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAsync from '../hooks/useAsync';
import { useToast } from '../context/ToastContext';
import { getProviders } from '../services/providerService';
import { getDevices } from '../services/deviceService';
import { requestQuotation } from '../services/quotationService';
import ProviderCard from '../components/providers/ProviderCard';
import Modal from '../components/ui/Modal';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

const FILTERS = [
  ['all', 'All'], ['technician', 'Technicians'], ['refurbisher', 'Refurbishers'],
  ['recycler', 'Recyclers'], ['supplier', 'Suppliers'],
];

export default function ProvidersPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [filter, setFilter] = useState('all');
  const { data, loading, error, reload } = useAsync(() => getProviders(filter), [filter]);
  const { data: devices } = useAsync(getDevices);

  const [quoteFor, setQuoteFor] = useState(null); // provider
  const [deviceId, setDeviceId] = useState('');
  const [problem, setProblem] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  function openQuote(provider) {
    setQuoteFor(provider);
    setDeviceId(devices?.[0]?.id || '');
    setProblem('');
    setDone(false);
  }

  async function submitQuoteRequest() {
    if (!deviceId) return;
    setSubmitting(true);
    try {
      await requestQuotation({ device_id: deviceId, provider_id: quoteFor.id, problem });
      setDone(true);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Providers</h1>
      <p className="page-sub">Discover verified repair, refurbish and recycling providers.</p>

      <div className="toolbar">
        {FILTERS.map(([val, lbl]) => (
          <button key={val} className={`chip ${filter === val ? 'active' : ''}`} onClick={() => setFilter(val)}>{lbl}</button>
        ))}
      </div>

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}
      {data && (
        <div className="grid grid-cards">
          {data.map((p) => (
            <ProviderCard key={p.id} provider={p} onRequestQuote={openQuote} />
          ))}
        </div>
      )}

      <Modal
        open={!!quoteFor}
        title={done ? 'Request sent' : `Request a quote — ${quoteFor?.name}`}
        onClose={() => setQuoteFor(null)}
        footer={done
          ? <Button onClick={() => navigate('/quotations')}>View my quotations</Button>
          : (
            <>
              <Button variant="secondary" onClick={() => setQuoteFor(null)}>Cancel</Button>
              <Button onClick={submitQuoteRequest} disabled={!deviceId || submitting}>{submitting ? 'Sending…' : 'Send request'}</Button>
            </>
          )}
      >
        {done ? (
          <p style={{ margin: 0 }}>Your quotation request was sent to {quoteFor?.name}. You'll see their quote under Quotations.</p>
        ) : !devices?.length ? (
          <p style={{ margin: 0 }}>Register a device first to request a quote.</p>
        ) : (
          <>
            <div className="field">
              <label>Device</label>
              <select className="select" value={deviceId} onChange={(e) => setDeviceId(e.target.value)}>
                {devices.map((d) => <option key={d.id} value={d.id}>{d.brand} {d.model}</option>)}
              </select>
            </div>
            <div className="field">
              <label>Describe the problem</label>
              <input className="input" value={problem} onChange={(e) => setProblem(e.target.value)} placeholder="e.g. cracked screen, weak battery" />
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}
