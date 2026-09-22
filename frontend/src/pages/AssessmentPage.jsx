// Condition assessment → recommendation (Phase 2 W4, FR-C + FR-D).
import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAsync from '../hooks/useAsync';
import { getDevice, assessDevice } from '../services/deviceService';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';
import RecommendationCard from '../components/devices/RecommendationCard';

// Radio group config for each condition dimension.
const GROUPS = [
  { key: 'screen',  label: 'Screen condition',  options: [['good', 'Good'], ['minor', 'Minor wear'], ['cracked', 'Cracked']] },
  { key: 'battery', label: 'Battery health',     options: [['good', 'Good'], ['weak', 'Weak'], ['dead', 'Dead']] },
  { key: 'body',    label: 'Body condition',     options: [['good', 'Good'], ['scratched', 'Scratched'], ['damaged', 'Damaged']] },
  { key: 'powers_on',    label: 'Powers on?',    options: [['yes', 'Yes'], ['no', 'No']] },
  { key: 'charging',     label: 'Charging works?', options: [['yes', 'Yes'], ['no', 'No']] },
  { key: 'water_damage', label: 'Water damage?',  options: [['no', 'No'], ['yes', 'Yes']] },
];

export default function AssessmentPage() {
  const { id } = useParams();
  const { data: device, loading, error } = useAsync(() => getDevice(id), [id]);

  const [form, setForm] = useState({
    screen: 'good', battery: 'good', body: 'good',
    powers_on: 'yes', charging: 'yes', water_damage: 'no', problems: '',
  });
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    const payload = {
      screen: form.screen, battery: form.battery, body: form.body,
      powers_on: form.powers_on === 'yes',
      charging: form.charging === 'yes',
      water_damage: form.water_damage === 'yes',
      problems: form.problems,
      age_years: new Date().getFullYear() - (device?.purchase_year || new Date().getFullYear()),
    };
    const res = await assessDevice(id, payload);
    setResult(res.recommendation);
    setSubmitting(false);
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div style={{ maxWidth: 680 }}>
      <Link to={`/devices/${id}`} className="back-link"><ChevronLeft size={16} /> Back to device</Link>
      <h1 className="page-title">Assess: {device.brand} {device.model}</h1>
      <p className="page-sub">Describe the condition to get a transparent circularity recommendation.</p>

      <form className="card" onSubmit={handleSubmit}>
        {GROUPS.map((g) => (
          <div className="field" key={g.key}>
            <label>{g.label}</label>
            <div className="radio-row">
              {g.options.map(([val, lbl]) => (
                <label className="radio-opt" key={val}>
                  <input type="radio" name={g.key} value={val} checked={form[g.key] === val} onChange={() => set(g.key, val)} />
                  <span>{lbl}</span>
                </label>
              ))}
            </div>
          </div>
        ))}

        <div className="field">
          <label>Functional problems (optional)</label>
          <input className="input" value={form.problems} onChange={(e) => set('problems', e.target.value)} placeholder="e.g. keyboard key sticks" />
        </div>

        <Button type="submit" disabled={submitting}>{submitting ? 'Evaluating…' : 'Get Recommendation'}</Button>
      </form>

      {result && (
        <div style={{ marginTop: 20 }}>
          <RecommendationCard recommendation={result} deviceId={id} />
        </div>
      )}
    </div>
  );
}
