import { NavLink, Outlet } from 'react-router-dom';
import './Layout.css';

const NAV_ITEMS = [
  { to: '/register', icon: '👤', label: 'Register Student' },
  { to: '/jobs/new', icon: '📋', label: 'Submit JD' },
  { to: '/results', icon: '🏆', label: 'Results' },
  { to: '/placement', icon: '📊', label: 'Placement' },
];

export default function Layout() {
  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <span className="logo-icon">◈</span>
          </div>
          <div>
            <h2 className="brand-name">Recruitment<br/><span className="text-gradient">Genie</span></h2>
            <p className="brand-tag">GitFind Platform</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link-active' : ''}`
              }
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className="status-dot" />
            <span>Mock API Active</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
