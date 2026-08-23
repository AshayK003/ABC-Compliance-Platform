import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const navigation = [
  { path: '/', label: 'Dashboard', icon: 'dashboard' },
  { path: '/centres', label: 'ABC Centres', icon: 'pets' },
  { path: '/surgeries', label: 'Surgeries', icon: 'medical_services' },
  { path: '/inspections', label: 'Inspections', icon: 'fact_check' },
  { path: '/funds', label: 'Fund Tracker', icon: 'account_balance_wallet' },
  { path: '/reports', label: 'Reports', icon: 'analytics' },
  { path: '/committee', label: 'Committee Portal', icon: 'groups' },
];

export function DashboardLayout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Close the mobile drawer whenever the route changes
  useEffect(() => {
    setDrawerOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2 rounded ${
      isActive
        ? 'text-primary font-bold bg-surface-container-highest dark:bg-surface-container-highest hover:bg-secondary-container dark:hover:bg-secondary-container transition-colors'
        : 'text-on-surface-variant dark:text-on-surface-variant hover:bg-secondary-container dark:hover:bg-secondary-container transition-colors'
    }`;

  return (
    <div className="bg-background text-on-surface font-body-md h-screen flex overflow-hidden">
      {/* Mobile top bar with menu button (hidden on lg+) */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-14 z-30 flex items-center justify-between px-4 bg-surface-container dark:bg-surface-container border-b border-outline-variant dark:border-outline-variant">
        <button
          type="button"
          aria-label="Open navigation menu"
          onClick={() => setDrawerOpen(true)}
          className="p-2 -ml-2 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
        >
          <span className="material-symbols-outlined">menu</span>
        </button>
        <h2 className="font-headline-sm text-[15px] leading-tight font-bold text-on-surface dark:text-on-surface truncate px-1">
          AWBI ABC Compliance
        </h2>
        <NavLink
          to="/profile"
          aria-label="Profile"
          className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center hover:bg-primary-container/80 transition-colors shrink-0"
        >
          <span className="material-symbols-outlined text-on-primary-container">person</span>
        </NavLink>
      </header>

      {/* Scrim for the mobile drawer */}
      {drawerOpen && (
        <div
          className="lg:hidden fixed inset-0 z-30 bg-black/50"
          onClick={() => setDrawerOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Side Navigation — fixed rail on lg+, slide-in drawer below lg */}
      <nav
        className={`fixed left-0 top-0 h-screen w-[216px] max-w-[80vw] bg-surface-container-high dark:bg-surface-container-high border-r border-outline-variant dark:border-outline-variant z-40 flex flex-col py-4 transition-transform duration-200 ease-out
          lg:translate-x-0 lg:z-20
          ${drawerOpen ? 'translate-x-0 shadow-xl' : '-translate-x-full'}`}
        aria-label="Primary"
      >
        <div className="px-3 mb-8 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <img src="/logo.svg" alt="ABC Compliance logo" className="w-9 h-9 rounded-lg shrink-0" />
            <div className="min-w-0">
              <h1 className="text-headline-sm font-headline-sm font-bold text-primary dark:text-primary truncate">ABC Digital</h1>
              <p className="font-label-md text-label-md text-on-surface-variant truncate">Compliance Platform</p>
            </div>
          </div>
          {/* Close button inside drawer (mobile only) */}
          <button
            type="button"
            aria-label="Close navigation menu"
            onClick={() => setDrawerOpen(false)}
            className="lg:hidden p-2 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <ul className="flex flex-col gap-1 px-1.5 flex-grow overflow-y-auto">
          {navigation.map((item) => (
            <li key={item.path}>
              <NavLink to={item.path} className={navLinkClass}>
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                  {item.icon}
                </span>
                <span className="font-label-md text-label-md">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="flex flex-col gap-1 px-2 mt-auto pt-4 border-t border-outline-variant/30">
          <NavLink
            to="/notifications"
            className="flex items-center gap-3 px-3 py-2 rounded text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-colors duration-200 ease-in-out cursor-pointer group"
          >
            <span className="material-symbols-outlined group-hover:text-primary transition-colors">notifications</span>
            <span className="font-label-md text-label-md">Notifications</span>
          </NavLink>
          <NavLink
            to="/settings"
            className="flex items-center gap-3 px-3 py-2 rounded text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-colors duration-200 ease-in-out cursor-pointer group"
          >
            <span className="material-symbols-outlined group-hover:text-primary transition-colors">settings</span>
            <span className="font-label-md text-label-md">Settings</span>
          </NavLink>
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded text-on-surface-variant font-medium hover:bg-error/10 hover:text-error transition-colors duration-200 ease-in-out cursor-pointer group w-full text-left"
          >
            <span className="material-symbols-outlined group-hover:text-error transition-colors">logout</span>
            <span className="font-label-md text-label-md">Sign Out</span>
          </button>
        </div>
      </nav>

      {/* Main Content Wrapper — full width under lg (mobile top bar), offset by rail on lg+ */}
      <div className="flex flex-col flex-1 w-full lg:ml-[216px] lg:w-[calc(100%-216px)] h-screen overflow-hidden pt-14 lg:pt-0">
        {/* Top App Bar (desktop only — mobile uses the fixed top bar above) */}
        <header className="hidden lg:flex justify-between items-center h-16 px-gutter bg-surface-container dark:bg-surface-container border-b border-outline-variant dark:border-outline-variant z-10 shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            <h2 className="font-headline-sm text-[17px] leading-snug font-black text-on-surface dark:text-on-surface truncate">
              AWBI ABC Compliance
            </h2>
          </div>
          <div className="flex items-center gap-4 text-on-surface-variant shrink-0">
            <NavLink
              to="/notifications"
              aria-label="Notifications"
              className="hover:text-primary dark:hover:text-primary transition-opacity duration-150 p-2 rounded-full hover:bg-surface-variant relative"
            >
              <span className="material-symbols-outlined">notifications</span>
            </NavLink>
            <NavLink
              to="/settings"
              aria-label="Settings"
              className="hover:text-primary dark:hover:text-primary transition-opacity duration-150 p-2 rounded-full hover:bg-surface-variant"
            >
              <span className="material-symbols-outlined">settings</span>
            </NavLink>
            <NavLink
              to="/profile"
              aria-label="Profile"
              className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center hover:bg-primary-container/80 transition-colors"
            >
              <span className="material-symbols-outlined text-on-primary-container">person</span>
            </NavLink>
          </div>
        </header>

        {/* Canvas */}
        <main className="flex-1 overflow-y-auto p-container-padding bg-background">
          <div className="max-w-7xl mx-auto flex flex-col gap-container-padding">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
