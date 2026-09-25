// Top bar (Phase 2 §2.2). The user chip is a menu that includes Log out — this is
// the ONLY logout affordance on mobile (the sidebar is hidden there), so login and
// logout work on both phone and desktop layouts.
import { useState, useRef, useEffect } from 'react';
import { Bell, LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

function initials(name = '') {
  return name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase() || 'U';
}

export default function Navbar() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Close the menu on outside click.
  useEffect(() => {
    function onClick(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  return (
    <header className="topbar">
      <strong style={{ color: 'var(--green-dark)' }}>Circular Electronics Marketplace</strong>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Bell size={18} color="var(--text-muted)" />
        <div className="user-menu" ref={ref}>
          <button className="user-chip" onClick={() => setOpen((o) => !o)} aria-haspopup="menu" aria-expanded={open}>
            <div className="avatar">{initials(user?.name)}</div>
            <div className="user-chip-text">
              <div style={{ fontWeight: 700, lineHeight: 1.1 }}>{user?.name}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{user?.role}</div>
            </div>
            <ChevronDown size={15} color="var(--text-muted)" />
          </button>
          {open && (
            <div className="user-dropdown" role="menu">
              <button className="dropdown-item" onClick={logout} role="menuitem">
                <LogOut size={16} /> Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
