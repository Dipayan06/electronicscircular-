// Login page (Phase 2 W1). PHASE 7: real authentication against the backend.
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Recycle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('demo.user@example.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate('/dashboard');
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
          <h1>Circular Electronics Marketplace</h1>
          <p>Give every device its highest-value next life</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>

          {error && <p style={{ color: 'var(--status-danger)', fontSize: 14, margin: '0 0 12px' }}>{error}</p>}

          <Button type="submit" block disabled={busy}>{busy ? 'Signing in…' : 'Log in'}</Button>
        </form>

        <hr className="divider" />
        <p style={{ textAlign: 'center', fontSize: 14, margin: 0 }}>
          New here? <Link to="/register">Create an account</Link>
        </p>
        <p className="auth-hint">Demo accounts (password123): demo.user@example.com · demo.provider@example.com · admin@example.com</p>
      </div>
    </div>
  );
}
