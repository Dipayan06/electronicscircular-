// Email verification (Feature 1). The user enters the 6-digit code sent to
// their inbox. Verification state comes only from the server (/auth/me) — the
// page never flips a flag locally. In dev mode (no mail server) the owner can
// reveal their own pending code.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MailCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { verifyEmail, resendVerification, getDevVerificationCode } from '../services/authService';
import Button from '../components/ui/Button';

export default function VerifyEmailPage() {
  const { user, refreshUser } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [devCode, setDevCode] = useState(null);

  if (user?.is_verified) {
    return (
      <div className="card" style={{ maxWidth: 460 }}>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <MailCheck color="var(--green)" /> Email verified
        </h1>
        <p className="page-sub" style={{ marginBottom: 14 }}>{user.email} is verified. You can buy and sell on the marketplace.</p>
        <Button onClick={() => navigate('/dashboard')}>Go to dashboard</Button>
      </div>
    );
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await verifyEmail(code.trim());
      await refreshUser();
      toast.success('Email verified');
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    try {
      await resendVerification();
      setDevCode(null);
      toast.success('A new code has been sent');
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function revealDevCode() {
    try {
      setDevCode(await getDevVerificationCode());
    } catch (err) {
      toast.error(err.message);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 460 }}>
      <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <MailCheck color="var(--green)" /> Verify your email
      </h1>
      <p className="page-sub" style={{ marginBottom: 16 }}>
        We sent a 6-digit code to <strong>{user?.email}</strong>. It expires in 10 minutes.
      </p>

      <form onSubmit={submit}>
        <div className="field">
          <label>Verification code</label>
          <input className="input" inputMode="numeric" autoComplete="one-time-code" maxLength={6}
                 placeholder="123456" value={code}
                 onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} required
                 style={{ letterSpacing: 6, fontSize: 20, fontWeight: 700 }} />
        </div>
        {error && <p style={{ color: 'var(--status-danger)', fontSize: 14, margin: '0 0 12px' }}>{error}</p>}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Button type="submit" disabled={busy || code.length !== 6}>{busy ? 'Verifying…' : 'Verify'}</Button>
          <Button type="button" variant="secondary" onClick={resend}>Resend code</Button>
        </div>
      </form>

      <div className="placeholder-note" style={{ marginTop: 16 }}>
        Development mode: no email server is connected, so codes go to a dev outbox.{' '}
        <button type="button" className="link-btn" onClick={revealDevCode}>Show my code</button>
        {devCode && <> — <strong style={{ letterSpacing: 2 }}>{devCode}</strong></>}
      </div>
    </div>
  );
}
