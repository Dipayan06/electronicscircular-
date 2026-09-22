// App shell (Phase 1 §1.2, Phase 2 §2.6): sidebar + top bar + routed content.
// <Outlet> is where the matched child route renders.
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import BottomNav from './BottomNav';

export default function AppLayout() {
  return (
    <div className="layout">
      <Sidebar />
      <div className="main">
        <Navbar />
        <div className="content">
          <Outlet />
        </div>
      </div>
      <BottomNav />
    </div>
  );
}
