import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AppShell from './AppShell';

export default function ProtectedLayout() {
  const { user, loading } = useAuth();

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--panel-bg)' }}>
      <div style={{ fontFamily: 'var(--f-mono)', color: 'var(--ink-faint)' }}>Loading…</div>
    </div>
  );

  if (!user) return <Navigate to="/login" replace />;

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}
