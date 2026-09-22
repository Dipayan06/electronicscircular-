// Mobile bottom navigation (Phase 2 §2.8). Shares nav.config with the sidebar.
import { NavLink } from 'react-router-dom';
import * as Icons from 'lucide-react';
import { NAV_ITEMS, BOTTOM_NAV } from '../../config/nav.config';
import { useAuth } from '../../context/AuthContext';

export default function BottomNav() {
  const { user } = useAuth();
  const role = user?.role || 'consumer';
  const items = NAV_ITEMS.filter(
    (i) => BOTTOM_NAV.includes(i.path) && i.roles.includes(role)
  );

  return (
    <nav className="bottom-nav">
      {items.map((item) => {
        const Icon = Icons[item.icon] || Icons.Circle;
        return (
          <NavLink key={item.path} to={item.path}>
            <Icon size={20} />
            <span>{item.label.replace('My ', '')}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
