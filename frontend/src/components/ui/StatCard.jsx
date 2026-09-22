// Stat card for dashboards (Phase 2 W2 / W10).
import * as Icons from 'lucide-react';

export default function StatCard({ value, label, icon }) {
  const Icon = icon && Icons[icon] ? Icons[icon] : Icons.Circle;
  return (
    <div className="card stat">
      <Icon className="stat-icon" size={20} />
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
