// Auth context — holds the current user + token and exposes login/register/logout.
// PHASE 7: now backed by the REAL backend (JWT). On load, if a token exists we
// verify it with GET /api/auth/me and restore the user; an invalid/expired token
// logs out. The token is stored under TOKEN_KEY and attached to every request by
// apiClient's interceptor (Phase 1 §1.2).
import { createContext, useContext, useState, useEffect } from 'react';
import { TOKEN_KEY } from '../services/apiClient';
import * as authService from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore + verify the session from a stored token.
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }
    authService
      .me()
      .then((u) => setUser(u))
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false));
  }, []);

  // Session expiry: apiClient dispatches 'cem:unauthorized' on a 401 from a
  // protected endpoint (e.g. an expired token). Log the user out so they return
  // to the login screen instead of seeing broken pages.
  useEffect(() => {
    function onUnauthorized() {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    }
    window.addEventListener('cem:unauthorized', onUnauthorized);
    return () => window.removeEventListener('cem:unauthorized', onUnauthorized);
  }, []);

  async function login(email, password) {
    const { token, user: u } = await authService.login(email, password);
    localStorage.setItem(TOKEN_KEY, token);
    setUser(u);
    return u;
  }

  async function register(data) {
    const { token, user: u } = await authService.register(data);
    localStorage.setItem(TOKEN_KEY, token);
    setUser(u);
    return u;
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }

  const value = { user, loading, isAuthenticated: !!user, login, register, logout };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
