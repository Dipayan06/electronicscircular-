// Consumer dashboard (Phase 2 W2). Now data-driven via dashboardService — counts
// reflect real store state (register a device and the count goes up).
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import useAsync from '../hooks/useAsync';
import { getDashboard } from '../services/dashboardService';
import StatCard from '../components/ui/StatCard';
import Button from '../components/ui/Button';
import LoadingState from '../components/ui/LoadingState';
import ErrorMessage from '../components/ui/ErrorMessage';

const STAT_META = [
  ['devices', 'My Devices', 'Smartphone'],
  ['activeRequests', 'Active Requests', 'Wrench'],
  ['pendingQuotes', 'Pending Quotes', 'FileText'],
  ['upcomingBookings', 'Upcoming Bookings', 'CalendarCheck'],
];

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync(getDashboard);

  return (
    <div>
      <h1 className="page-title">Welcome back, {user?.name} 👋</h1>
      <p className="page-sub">Here's the state of your devices and circular activity.</p>

      {loading && <LoadingState />}
      {error && <ErrorMessage message={error} onRetry={reload} />}

      {data && (
        <>
          <div className="grid grid-stats" style={{ marginBottom: 24 }}>
            {STAT_META.map(([key, label, icon]) => (
              <StatCard key={key} value={data.stats[key]} label={label} icon={icon} />
            ))}
          </div>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 26 }}>
            <Button onClick={() => navigate('/devices/new')}>+ Register Device</Button>
            <Button variant="secondary" onClick={() => navigate('/marketplace')}>Browse Marketplace</Button>
            <Button variant="secondary" onClick={() => navigate('/providers')}>Find Providers</Button>
          </div>

          <div className="card">
            <h2 style={{ fontSize: 17, marginBottom: 8 }}>Recent Activity</h2>
            {data.activity.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No activity yet.</p>}
            {data.activity.map((a, i) => (
              <div className="feed-item" key={i}>
                <span className="feed-dot" />
                <span>{a.text}</span>
                <span className="feed-time">{a.time}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
