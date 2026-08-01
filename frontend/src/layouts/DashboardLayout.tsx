import { Outlet, NavLink, useNavigate } from 'react-router-dom';
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

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="bg-background text-on-surface font-body-md h-screen flex overflow-hidden">
      {/* Side Navigation */}
      <nav className="fixed left-0 top-0 h-screen w-[240px] bg-surface-container-high dark:bg-surface-container-high border-r border-outline-variant dark:border-outline-variant z-20 flex flex-col py-4 transition-all duration-200 ease-in-out">
        <div className="px-gutter mb-8 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-on-primary font-headline-sm font-bold">
            A
          </div>
          <div>
            <h1 className="text-headline-sm font-headline-sm font-bold text-primary dark:text-primary">ABC Digital</h1>
            <p className="font-label-md text-label-md text-on-surface-variant">Compliance Platform</p>
          </div>
        </div>
        <ul className="flex flex-col gap-1 px-2 flex-grow">
          {navigation.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded ${
                    isActive
                      ? 'text-primary font-bold bg-surface-container-highest dark:bg-surface-container-highest hover:bg-secondary-container dark:hover:bg-secondary-container transition-colors'
                      : 'text-on-surface-variant dark:text-on-surface-variant hover:bg-secondary-container dark:hover:bg-secondary-container transition-colors'
                  }`
                }
              >
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                  {item.icon}
                </span>
                <span className="font-label-md text-label-md">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="flex flex-col gap-1 px-3 mt-auto pt-4 border-t border-outline-variant/30">
          <NavLink
            to="/notifications"
            className="flex items-center gap-3 px-3 py-2 rounded text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-all duration-200 ease-in-out cursor-pointer group"
          >
            <span className="material-symbols-outlined group-hover:text-primary transition-colors">notifications</span>
            <span className="font-label-md text-label-md">Notifications</span>
          </NavLink>
          <NavLink
            to="/settings"
            className="flex items-center gap-3 px-3 py-2 rounded text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-all duration-200 ease-in-out cursor-pointer group"
          >
            <span className="material-symbols-outlined group-hover:text-primary transition-colors">settings</span>
            <span className="font-label-md text-label-md">Settings</span>
          </NavLink>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded text-on-surface-variant font-medium hover:bg-error/10 hover:text-error transition-all duration-200 ease-in-out cursor-pointer group w-full text-left"
          >
            <span className="material-symbols-outlined group-hover:text-error transition-colors">logout</span>
            <span className="font-label-md text-label-md">Sign Out</span>
          </button>
        </div>
      </nav>

      {/* Main Content Wrapper */}
      <div className="flex flex-col flex-1 ml-[240px] w-[calc(100%-240px)] h-screen overflow-hidden">
        {/* Top App Bar */}
        <header className="flex justify-between items-center h-16 px-gutter bg-surface-container dark:bg-surface-container border-b border-outline-variant dark:border-outline-variant z-10 shrink-0">
          <div className="flex items-center gap-4">
            <h2 className="text-headline-sm font-headline-sm font-black text-on-surface dark:text-on-surface">AWBI ABC Compliance</h2>
          </div>
          <div className="flex items-center gap-4 text-on-surface-variant">
            <NavLink
              to="/notifications"
              className="hover:text-primary dark:hover:text-primary transition-opacity duration-150 p-2 rounded-full hover:bg-surface-variant relative"
            >
              <span className="material-symbols-outlined">notifications</span>
              {/* Unread badge would go here */}
            </NavLink>
            <NavLink
              to="/settings"
              className="hover:text-primary dark:hover:text-primary transition-opacity duration-150 p-2 rounded-full hover:bg-surface-variant"
            >
              <span className="material-symbols-outlined">settings</span>
            </NavLink>
            <NavLink
              to="/profile"
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