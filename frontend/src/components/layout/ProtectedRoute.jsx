// Route guard (Phase 1 §1.7, Phase 2 §2.7): redirects unauthenticated users to
// /login. Wraps the whole authenticated area of the app.
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoadingState from '../ui/LoadingState';

export default function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <LoadingState label="Checking session…" />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Outlet />;
}
