import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { NavLink, useNavigate } from 'react-router-dom';

export function CommitteePortal() {
  const [loading, setLoading] = useState(true);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(false);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-background font-body-md text-body-md">
      {/* Mobile Top App Bar */}
      <header className="md:hidden w-full sticky top-0 z-40 bg-surface-container border-b border-outline-variant flex justify-between items-center h-16 px-gutter">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center">
            <span className="material-symbols-outlined text-on-primary-container icon-fill text-lg">gavel</span>
          </div>
          <span className="font-headline-md text-headline-md font-bold text-primary">ABC Digital</span>
        </div>
        <div className="flex gap-4">
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer active:opacity-80 transition-opacity">search</span>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer active:opacity-80 transition-opacity">notifications</span>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer active:opacity-80 transition-opacity text-[24px]">person</span>
        </div>
      </header>

      {/* Side Navigation Bar */}
      <nav className="hidden md:flex w-[240px] h-screen sticky left-0 top-0 bg-surface-container-low border-r border-outline-variant flex-col py-4 z-40 shrink-0">
        <div className="px-6 mb-8 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary icon-fill">gavel</span>
          </div>
          <div>
            <div className="font-headline-sm text-headline-sm font-black text-on-surface">ABC Digital</div>
            <div className="font-label-bold text-label-bold text-on-surface-variant tracking-wider uppercase">Gov Compliance</div>
          </div>
        </div>
        <div className="flex-1 flex flex-col gap-1 px-3">
          <NavLink
            to="/"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-all duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px]">dashboard</span>
            <span>Dashboard</span>
          </NavLink>
          <NavLink
            to="/inspections"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-primary font-bold bg-secondary-container/10 hover:bg-secondary-container/20 transition-all duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px] icon-fill">gavel</span>
            <span>Compliance Risk</span>
          </NavLink>
          <NavLink
            to="/reports"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-all duration-200 ease-in-out font-label-bold text-label-bold"
            end
          >
            <span className="material-symbols-outlined text-[20px]">history_edu</span>
            <span>Audit Logs</span>
          </NavLink>
          <NavLink
            to="/settings"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-all duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px]">security</span>
            <span>Entity Monitor</span>
          </NavLink>
          <NavLink
            to="/reports"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-all duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px]">analytics</span>
            <span>Reports</span>
          </NavLink>
        </div>
        <div className="px-3 pt-4 border-t border-outline-variant/30 flex flex-col gap-1">
          <NavLink
            to="/settings"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-all duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px]">settings</span>
            <span>Settings</span>
          </NavLink>
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-error/10 hover:text-error transition-all duration-200 ease-in-out font-label-bold text-label-bold w-full text-left"
          >
            <span className="material-symbols-outlined">logout</span>
            <span>Sign Out</span>
          </button>
        </div>
      </nav>

      {/* Main Content Canvas */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Desktop Top Bar */}
        <div className="hidden md:flex h-16 border-b border-outline-variant bg-surface-container px-container-padding items-center justify-between sticky top-0 z-30">
          <h1 className="font-headline-sm text-headline-sm text-on-surface">Committee Portal</h1>
          <div className="flex items-center gap-4">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
              <input className="bg-background border border-outline-variant rounded-DEFAULT pl-9 pr-4 py-1.5 text-body-sm font-body-sm text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all w-64 placeholder:text-on-surface-variant/50" placeholder="Search repository..." type="text" />
            </div>
            <NavLink
              to="/notifications"
              className="w-8 h-8 rounded-DEFAULT hover:bg-surface-container-high flex items-center justify-center text-on-surface-variant transition-colors relative"
            >
              <span className="material-symbols-outlined">notifications</span>
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-error rounded-full"></span>
            </NavLink>
            <NavLink
              to="/settings"
              className="w-8 h-8 rounded-DEFAULT hover:bg-surface-container-high flex items-center justify-center text-on-surface-variant transition-colors"
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
        </div>

        <div className="p-container-padding flex flex-col gap-6 w-full max-w-[1600px] mx-auto overflow-x-hidden">
          {/* Bento Grid Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Decision Log (Spans 8 columns) */}
            <div className="lg:col-span-8 bg-surface border border-outline-variant rounded-lg flex flex-col overflow-hidden">
              <div className="px-5 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">how_to_vote</span>
                  <h2 className="font-headline-sm text-headline-sm text-on-surface">Decision Log</h2>
                </div>
                <button className="text-primary hover:text-primary-fixed font-label-bold text-label-bold flex items-center gap-1 transition-colors">
                  View All <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container border-b border-outline-variant">
                      <th className="p-table-cell-padding font-label-bold text-label-bold text-on-surface-variant uppercase tracking-wider">Resolution ID</th>
                      <th className="p-table-cell-padding font-label-bold text-label-bold text-on-surface-variant uppercase tracking-wider">Subject</th>
                      <th className="p-table-cell-padding font-label-bold text-label-bold text-on-surface-variant uppercase tracking-wider">Status</th>
                      <th className="p-table-cell-padding font-label-bold text-label-bold text-on-surface-variant uppercase tracking-wider text-right">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/50">
                    <tr className="hover:bg-surface-container-low transition-colors">
                      <td className="p-table-cell-padding font-code-sm text-code-sm text-tertiary">RES-2023-142</td>
                      <td className="p-table-cell-padding font-body-md text-body-md text-on-surface">Data Retention Policy Amendment</td>
                      <td className="p-table-cell-padding">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-sm bg-primary-container/20 text-primary font-label-bold text-label-bold border border-primary/20">Passed</span>
                      </td>
                      <td className="p-table-cell-padding text-right font-code-sm text-code-sm text-on-surface">9 - 2 - 1</td>
                    </tr>
                    <tr className="hover:bg-surface-container-low transition-colors">
                      <td className="p-table-cell-padding font-code-sm text-code-sm text-tertiary">RES-2023-141</td>
                      <td className="p-table-cell-padding font-body-md text-body-md text-on-surface">Q3 Audit Framework Approval</td>
                      <td className="p-table-cell-padding">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-sm bg-error-container/20 text-error font-label-bold text-label-bold border border-error/20">Rejected</span>
                      </td>
                      <td className="p-table-cell-padding text-right font-code-sm text-code-sm text-on-surface">4 - 7 - 1</td>
                    </tr>
                    <tr className="hover:bg-surface-container-low transition-colors">
                      <td className="p-table-cell-padding font-code-sm text-code-sm text-tertiary">RES-2023-140</td>
                      <td className="p-table-cell-padding font-body-md text-body-md text-on-surface">Vendor Risk Assessment Guidelines</td>
                      <td className="p-table-cell-padding">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-sm bg-secondary-container/40 text-on-secondary-container font-label-bold text-label-bold border border-outline-variant">Pending</span>
                      </td>
                      <td className="p-table-cell-padding text-right font-code-sm text-code-sm text-on-surface-variant">N/A</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Upcoming Meetings (Spans 4 columns) */}
            <div className="lg:col-span-4 bg-surface border border-outline-variant rounded-lg flex flex-col overflow-hidden">
              <div className="px-5 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">calendar_month</span>
                  <h2 className="font-headline-sm text-headline-sm text-on-surface">Schedule</h2>
                </div>
              </div>
              <div className="p-4 flex flex-col gap-4">
                <div className="flex gap-4 p-3 rounded-DEFAULT border border-outline-variant/50 bg-surface-container-lowest hover:border-primary/50 transition-colors cursor-pointer">
                  <div className="flex flex-col items-center justify-center w-12 h-12 bg-surface-container rounded-sm border border-outline-variant shrink-0">
                    <span className="font-label-bold text-label-bold text-error uppercase">Oct</span>
                    <span className="font-headline-md text-headline-md font-bold text-on-surface leading-none">24</span>
                  </div>
                  <div className="flex flex-col justify-center">
                    <h3 className="font-body-md text-body-md font-semibold text-on-surface line-clamp-1">Quarterly Review Board</h3>
                    <div className="flex items-center gap-1 text-on-surface-variant font-label-md text-label-md mt-1">
                      <span className="material-symbols-outlined text-[14px]">schedule</span>
                      <span>10:00 AM EST</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-4 p-3 rounded-DEFAULT border border-outline-variant/50 bg-surface-container-lowest hover:border-primary/50 transition-colors cursor-pointer">
                  <div className="flex flex-col items-center justify-center w-12 h-12 bg-surface-container rounded-sm border border-outline-variant shrink-0">
                    <span className="font-label-bold text-label-bold text-on-surface-variant uppercase">Nov</span>
                    <span className="font-headline-md text-headline-md font-bold text-on-surface leading-none">02</span>
                  </div>
                  <div className="flex flex-col justify-center">
                    <h3 className="font-body-md text-body-md font-semibold text-on-surface line-clamp-1">Policy Draft Committee</h3>
                    <div className="flex items-center gap-1 text-on-surface-variant font-label-md text-label-md mt-1">
                      <span className="material-symbols-outlined text-[14px]">videocam</span>
                      <span>Virtual • 2:00 PM EST</span>
                    </div>
                  </div>
                </div>
                <button
                type="button"
                className="w-full py-2 border border-outline-variant rounded-DEFAULT text-on-surface font-label-bold text-label-bold hover:bg-surface-container transition-colors mt-2"
              >
                  Sync Calendar
                </button>
              </div>
            </div>

            {/* Document Repository (Spans 6 columns) */}
            <div className="lg:col-span-6 bg-surface border border-outline-variant rounded-lg flex flex-col overflow-hidden">
              <div className="px-5 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">folder_special</span>
                  <h2 className="font-headline-sm text-headline-sm text-on-surface">Repository</h2>
                </div>
                <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-on-surface">more_horiz</span>
              </div>
              <div className="p-4 grid grid-cols-2 gap-3">
                <div className="flex items-center gap-3 p-3 rounded-DEFAULT border border-outline-variant hover:bg-surface-container-high transition-colors cursor-pointer group">
                  <span className="material-symbols-outlined text-tertiary text-[24px] group-hover:text-primary transition-colors">description</span>
                  <div className="flex flex-col overflow-hidden">
                    <span className="font-body-md text-body-md text-on-surface truncate">Draft_Policy_v4.pdf</span>
                    <span className="font-label-md text-label-md text-on-surface-variant">Updated 2h ago</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-DEFAULT border border-outline-variant hover:bg-surface-container-high transition-colors cursor-pointer group">
                  <span className="material-symbols-outlined text-tertiary text-[24px] group-hover:text-primary transition-colors">description</span>
                  <div className="flex flex-col overflow-hidden">
                    <span className="font-body-md text-body-md text-on-surface truncate">Q3_Minutes_Final.docx</span>
                    <span className="font-label-md text-label-md text-on-surface-variant">Updated 1d ago</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-DEFAULT border border-outline-variant hover:bg-surface-container-high transition-colors cursor-pointer group">
                  <span className="material-symbols-outlined text-tertiary text-[24px] group-hover:text-primary transition-colors">folder</span>
                  <div className="flex flex-col overflow-hidden">
                    <span className="font-body-md text-body-md text-on-surface truncate">Archive 2022</span>
                    <span className="font-label-md text-label-md text-on-surface-variant">14 items</span>
                  </div>
                </div>
                <div className="flex items-center justify-center p-3 rounded-DEFAULT border border-dashed border-outline-variant hover:border-primary/50 hover:bg-primary/5 transition-colors cursor-pointer text-on-surface-variant hover:text-primary">
                  <div className="flex items-center gap-2 font-label-bold text-label-bold">
                    <span className="material-symbols-outlined text-[18px]">upload</span>
                    <span>Upload File</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Member Directory (Spans 6 columns) */}
            <div className="lg:col-span-6 bg-surface border border-outline-variant rounded-lg flex flex-col overflow-hidden">
              <div className="px-5 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">group</span>
                  <h2 className="font-headline-sm text-headline-sm text-on-surface">Directory</h2>
                </div>
              </div>
              <div className="p-4 flex flex-col gap-3">
                <div className="flex items-center justify-between p-2 rounded-DEFAULT hover:bg-surface-container transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center border border-outline-variant">
                      <span className="material-symbols-outlined text-on-primary-container icon-fill text-xl">person</span>
                    </div>
                    <div>
                      <div className="font-body-md text-body-md font-semibold text-on-surface">Arthur Pendelton</div>
                      <div className="font-label-md text-label-md text-on-surface-variant">Chairperson</div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                  type="button"
                  className="w-8 h-8 rounded-DEFAULT bg-surface-container border border-outline-variant flex items-center justify-center text-on-surface-variant hover:text-primary hover:border-primary transition-colors"
                >
                      <span className="material-symbols-outlined text-[16px]">mail</span>
                    </button>
                    <button
                  type="button"
                  className="w-8 h-8 rounded-DEFAULT bg-surface-container border border-outline-variant flex items-center justify-center text-on-surface-variant hover:text-primary hover:border-primary transition-colors"
                >
                      <span className="material-symbols-outlined text-[16px]">call</span>
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between p-2 rounded-DEFAULT hover:bg-surface-container transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center border border-outline-variant">
                      <span className="material-symbols-outlined text-on-secondary-container icon-fill text-xl">person</span>
                    </div>
                    <div>
                      <div className="font-body-md text-body-md font-semibold text-on-surface">Elena Rostova</div>
                      <div className="font-label-md text-label-md text-on-surface-variant">Chief Ethics Officer</div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                  type="button"
                  className="w-8 h-8 rounded-DEFAULT bg-surface-container border border-outline-variant flex items-center justify-center text-on-surface-variant hover:text-primary hover:border-primary transition-colors"
                >
                      <span className="material-symbols-outlined text-[16px]">mail</span>
                    </button>
                    <button
                  type="button"
                  className="w-8 h-8 rounded-DEFAULT bg-surface-container border border-outline-variant flex items-center justify-center text-on-surface-variant hover:text-primary hover:border-primary transition-colors"
                >
                      <span className="material-symbols-outlined text-[16px]">call</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}