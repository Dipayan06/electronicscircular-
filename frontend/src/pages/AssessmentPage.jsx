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
import { parseAssessment } from '../services/assistantService';

const yesNo = (b) => (b ? 'yes' : 'no');

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

  const [story, setStory] = useState('');
  const [parsing, setParsing] = useState(false);
  const [filled, setFilled] = useState(null); // null | 'model' | 'rules' | error message

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  // The assistant turns a free-text description into the answers below. It's a
  // pre-fill only: the user checks the radios before asking for a recommendation.
  async function fillFromStory() {
    setParsing(true);
    try {
      const { assessment: a, source } = await parseAssessment(story);
      setForm((f) => ({
        ...f, screen: a.screen, battery: a.battery, body: a.body,
        powers_on: yesNo(a.powers_on), charging: yesNo(a.charging), water_damage: yesNo(a.water_damage),
        problems: f.problems || story.slice(0, 500),
      }));
      setFilled(source);
      setResult(null);
    } catch (err) {
      setFilled(err.message);
    } finally {
      setParsing(false);
    }
  }

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
        <div className="assist-box">
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor="story">Describe the problem in your own words (optional)</label>
            <textarea id="story" className="input textarea" value={story} maxLength={600}
                      onChange={(e) => setStory(e.target.value)}
                      placeholder="e.g. The screen cracked when I dropped it and the battery drains really fast" />
          </div>
          <div className="assist-row">
            <Button type="button" variant="secondary" onClick={fillFromStory} disabled={parsing || story.trim().length < 3}>
              {parsing ? 'Reading…' : 'Fill in the answers for me'}
            </Button>
            {filled === 'model' || filled === 'rules' ? (
              <span className="assist-note" role="status">
                Answers filled in by the assistant{filled === 'rules' ? ' (keyword fallback)' : ''}. Check them before continuing.
              </span>
            ) : filled && <span className="assist-note" role="alert">{filled}</span>}
          </div>
        </div>

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
