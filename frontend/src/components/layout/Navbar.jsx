// Top bar (Phase 2 §2.2): brand on mobile, and the current-user chip.
import { Bell } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

function initials(name = '') {
  return name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase() || 'U';
}

export default function Navbar() {
  const { user } = useAuth();
  return (
    <header className="topbar">
      <strong style={{ color: 'var(--green-dark)' }}>Circular Electronics Marketplace</strong>
      <div className="topbar-user">
        <Bell size={18} color="var(--text-muted)" />
        <div className="avatar">{initials(user?.name)}</div>
        <div>
          <div style={{ fontWeight: 700, lineHeight: 1.1 }}>{user?.name}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{user?.role}</div>
        </div>
      </div>
    </header>
  );
}
