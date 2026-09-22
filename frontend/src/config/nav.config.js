// Single source of truth for navigation (Phase 2 §2.2).
// Both the desktop sidebar and the mobile bottom nav read from this.
// `roles` lists which user roles see each item — this drives the role-aware
// navigation. Icon names refer to lucide-react icons.

export const NAV_ITEMS = [
  { label: 'Dashboard',   path: '/dashboard',   icon: 'LayoutDashboard', roles: ['consumer', 'provider', 'refurbisher', 'recycler', 'supplier', 'admin'] },
  { label: 'My Devices',  path: '/devices',     icon: 'Smartphone',      roles: ['consumer'] },
  { label: 'Providers',   path: '/providers',   icon: 'Wrench',          roles: ['consumer'] },
  { label: 'Quotations',  path: '/quotations',  icon: 'FileText',        roles: ['consumer', 'provider'] },
  { label: 'Bookings',    path: '/bookings',    icon: 'CalendarCheck',   roles: ['consumer', 'provider'] },
  { label: 'Marketplace', path: '/marketplace', icon: 'Store',           roles: ['consumer', 'refurbisher', 'admin'] },
  { label: 'Collection',  path: '/collection',  icon: 'Recycle',         roles: ['consumer', 'recycler'] },
  { label: 'Admin Panel', path: '/admin',       icon: 'ShieldCheck',     roles: ['admin'] },
];

// A compact subset shown in the mobile bottom bar.
export const BOTTOM_NAV = ['/dashboard', '/devices', '/marketplace', '/providers'];

export function navForRole(role) {
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}
