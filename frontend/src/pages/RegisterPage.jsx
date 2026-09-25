// Registration page (Phase 2 W1 variant). PHASE 7: real registration (POST
// /api/auth/register) — creates a hashed account and logs in with a JWT.
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Recycle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';

const ROLES = ['consumer', 'provider', 'refurbisher', 'recycler', 'supplier'];

// UX hint only — the server enforces the same rule and is the real boundary.
const ALLOWED_DOMAINS = ['gmail.com', 'yahoo.com'];
const domainOk = (email) => ALLOWED_DOMAINS.includes(email.trim().toLowerCase().split('@')[1] || '');

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'consumer' });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    if (!domainOk(form.email)) {
      setError('Please use a @gmail.com or @yahoo.com email address.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await register(form);
      navigate('/verify-email');
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <div className="auth-logo">
          <Recycle className="mark" size={34} color="var(--green)" />
          <h1>Create your account</h1>
          <p>Join the circular electronics platform</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Full name</label>
            <input className="input" value={form.name} onChange={update('name')} minLength={2} required />
          </div>
          <div className="field">
            <label>Email</label>
            <input className="input" type="email" value={form.email} onChange={update('email')}
                   placeholder="you@gmail.com" required />
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              Only @gmail.com and @yahoo.com addresses are accepted. We'll send a verification code.
            </div>
          </div>
          <div className="field">
            <label>Password</label>
            <input className="input" type="password" value={form.password} onChange={update('password')} minLength={6} required />
          </div>
          <div className="field">
            <label>I am a</label>
            <select className="select" value={form.role} onChange={update('role')}>
              {ROLES.map((r) => (
                <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
              ))}
            </select>
          </div>

          {error && <p style={{ color: 'var(--status-danger)', fontSize: 14, margin: '0 0 12px' }}>{error}</p>}

          <Button type="submit" block disabled={busy}>{busy ? 'Creating…' : 'Create account'}</Button>
        </form>

        <hr className="divider" />
        <p style={{ textAlign: 'center', fontSize: 14, margin: 0 }}>
          Already registered? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
