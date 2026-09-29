// App shell (Phase 1 §1.2, Phase 2 §2.6): sidebar + top bar + routed content.
// <Outlet> is where the matched child route renders.
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import BottomNav from './BottomNav';
import AssistantChat from '../assistant/AssistantChat';

export default function AppLayout() {
  const { user } = useAuth();
  const { pathname } = useLocation();
  // Feature 1: unverified accounts can browse but not buy/sell (enforced by the API).
  const showVerifyBanner = user && !user.is_verified && pathname !== '/verify-email';

  return (
    <div className="layout">
      <Sidebar />
      <div className="main">
        <Navbar />
        <div className="content">
          {showVerifyBanner && (
            <div className="verify-banner">
              Verify your email to buy or sell on the marketplace. <Link to="/verify-email">Verify now</Link>
            </div>
          )}
          <Outlet />
        </div>
      </div>
      <BottomNav />
      <AssistantChat />
    </div>
  );
}
