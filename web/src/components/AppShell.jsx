import { AlertTriangle } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { List, Clipboard, MapPin, Activity, LogOut, Zap } from 'lucide-react';

const NAV_ITEMS = [
  { path: '/risk-queue',    label: 'Risk Queue',        Icon: List },
  { path: '/cases',         label: 'Case List',         Icon: Clipboard },
  { path: '/feeder-map',    label: 'Feeder Map',        Icon: MapPin },
  { path: '/analytics',     label: 'Model Performance', Icon: Activity },
];

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const initials = user?.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() ?? '??';
  const roleLabel = {
    officer: 'Revenue Protection Officer',
    inspector: 'Field Inspector',
    circle_manager: 'Circle Manager',
  }[user?.role] ?? user?.role;

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className="shell">
      {/* TOPBAR */}
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><Zap size={16} /></div>
          <div className="brand-text">
            <b>GRID-GUARD AI</b>
            <span>Revenue Protection Console</span>
          </div>
        </div>
        <div className="topbar-right">
          <div className="sys-led-cluster">
            <span className="sys-led" />
            SYSTEM NOMINAL
          </div>
          <div className="user-chip">
            <div className="user-avatar">{initials}</div>
            <div>
              <div className="user-name">{user?.name}</div>
              <span className="user-role">{roleLabel}</span>
            </div>
          </div>
          <button className="signout-btn" onClick={handleLogout}>
            <LogOut size={13} /> Sign out
          </button>
        </div>
      </header>

      {/* DEMO BANNER */}
      <div className="demo-banner">
        <div className="inner">
          <AlertTriangle size={15} />
          <span>Demo / benchmark data — not live DISCO data</span>
        </div>
      </div>

      {/* SIDENAV */}
      <nav className="sidenav">
        {NAV_ITEMS.map(({ path, label, Icon }) => (
          <button
            key={path}
            className={`nav-btn${location.pathname === path ? ' active' : ''}`}
            onClick={() => navigate(path)}
          >
            <Icon size={17} />
            {label}
            <span className="nav-dot" />
          </button>
        ))}
        <div className="sidenav-foot">
          IESCO Circle 4<br />
          Session active · v1.0 demo
        </div>
      </nav>

      {/* MAIN */}
      <main className="main">{children}</main>
    </div>
  );
}
