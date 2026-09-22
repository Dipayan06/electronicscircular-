// Role-aware sidebar (Phase 2 §2.2). Reads nav items from nav.config and filters
// by the current user's role.
import { NavLink } from 'react-router-dom';
import * as Icons from 'lucide-react';
import { navForRole } from '../../config/nav.config';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const items = navForRole(user?.role || 'consumer');

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <Icons.Recycle size={22} color="var(--green)" />
        <span>Circular</span>
      </div>

      <nav>
        {items.map((item) => {
          const Icon = Icons[item.icon] || Icons.Circle;
          return (
            <NavLink key={item.path} to={item.path} className="nav-link">
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-spacer" />

      <button className="nav-link" onClick={logout} style={{ border: 'none', background: 'none', cursor: 'pointer', width: '100%' }}>
        <Icons.LogOut size={18} />
        <span>Log out</span>
      </button>
    </aside>
  );
}
