// Application router (Phase 1 route list, Phase 2 sitemap).
// Phase 4: every feature route now renders a real, functional page backed by the
// mock service layer. Public routes sit outside the auth guard; everything else
// is wrapped in <ProtectedRoute> + <AppLayout>.
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import ProtectedRoute from './components/layout/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import DevicesPage from './pages/DevicesPage';
import DeviceFormPage from './pages/DeviceFormPage';
import DeviceDetailPage from './pages/DeviceDetailPage';
import AssessmentPage from './pages/AssessmentPage';
import ProvidersPage from './pages/ProvidersPage';
import ProviderDetailPage from './pages/ProviderDetailPage';
import QuotationsPage from './pages/QuotationsPage';
import BookingsPage from './pages/BookingsPage';
import MarketplacePage from './pages/MarketplacePage';
import ListingDetailPage from './pages/ListingDetailPage';
import ListDevicePage from './pages/ListDevicePage';
import CollectionPage from './pages/CollectionPage';
import LifecyclePage from './pages/LifecyclePage';
import AdminPage from './pages/AdminPage';
import VerifyEmailPage from './pages/VerifyEmailPage';

export default function App() {
  return (
    <ToastProvider>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* authenticated area */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />

              <Route path="/devices" element={<DevicesPage />} />
              <Route path="/devices/new" element={<DeviceFormPage />} />
              <Route path="/devices/:id" element={<DeviceDetailPage />} />
              <Route path="/devices/:id/assessment" element={<AssessmentPage />} />

              <Route path="/providers" element={<ProvidersPage />} />
              <Route path="/providers/:id" element={<ProviderDetailPage />} />

              <Route path="/quotations" element={<QuotationsPage />} />
              <Route path="/bookings" element={<BookingsPage />} />

              <Route path="/marketplace" element={<MarketplacePage />} />
              <Route path="/marketplace/:id" element={<ListingDetailPage />} />
              <Route path="/list-device" element={<ListDevicePage />} />

              <Route path="/collection" element={<CollectionPage />} />
              <Route path="/lifecycle/:deviceId" element={<LifecyclePage />} />

              <Route path="/admin" element={<AdminPage />} />
            </Route>
          </Route>

          {/* defaults */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </ToastProvider>
  );
}
