import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { NavLink, useNavigate } from 'react-router-dom';
import { api } from '../services/api';

type DecisionRow = {
  id: string;
  resolution_id: string;
  subject: string;
  status: string;
  tally: { yes: number; no: number; abstain: number };
};

type MeetingRow = {
  id: string;
  title: string;
  scheduled_at: string;
  location: string | null;
  meeting_type: string;
  status: string;
};

type DocumentRow = {
  id: string;
  title: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
};

type MemberRow = {
  id: string;
  name: string;
  phone: string;
  role: string;
};

function statusBadge(status: string) {
  if (status === 'passed') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-sm bg-primary-container/20 text-primary font-label-bold text-label-bold border border-primary/20">Passed</span>
    );
  }
  if (status === 'rejected') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-sm bg-error-container/20 text-error font-label-bold text-label-bold border border-error/20">Rejected</span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-sm bg-secondary-container/40 text-on-secondary-container font-label-bold text-label-bold border border-outline-variant">Pending</span>
  );
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function CommitteePortal() {
  const [loading, setLoading] = useState(true);
  const [decisions, setDecisions] = useState<DecisionRow[]>([]);
  const [meetings, setMeetings] = useState<MeetingRow[]>([]);
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [members, setMembers] = useState<MemberRow[]>([]);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.getCommitteeDecisions().catch(() => [] as DecisionRow[]),
      api.getCommitteeMeetings().catch(() => [] as MeetingRow[]),
      api.getCommitteeDocuments().catch(() => [] as DocumentRow[]),
      api.getCommitteeMembers().catch(() => [] as MemberRow[]),
    ])
      .then(([d, m, docs, mem]) => {
        if (cancelled) return;
        setDecisions(d);
        setMeetings(m);
        setDocuments(docs);
        setMembers(mem);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
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
    <div className="flex min-h-screen">
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
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-colors duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px]">dashboard</span>
            <span>Dashboard</span>
          </NavLink>
          <NavLink
            to="/inspections"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-primary font-bold bg-secondary-container/10 hover:bg-secondary-container/20 transition-colors duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px] icon-fill">gavel</span>
            <span>Compliance Risk</span>
          </NavLink>
          <NavLink
            to="/reports"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-colors duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px]">history_edu</span>
            <span>Audit Logs</span>
          </NavLink>
          <NavLink
            to="/settings"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-colors duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px]">security</span>
            <span>Entity Monitor</span>
          </NavLink>
        </div>
        <div className="px-3 pt-4 border-t border-outline-variant/30 flex flex-col gap-1">
          <NavLink
            to="/settings"
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-secondary-container/20 transition-colors duration-200 ease-in-out font-label-bold text-label-bold"
          >
            <span className="material-symbols-outlined text-[20px]">settings</span>
            <span>Settings</span>
          </NavLink>
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-DEFAULT text-on-surface-variant font-medium hover:bg-error/10 hover:text-error transition-colors duration-200 ease-in-out font-label-bold text-label-bold w-full text-left"
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
            <NavLink
              to="/notifications"
              className="w-8 h-8 rounded-DEFAULT hover:bg-surface-container-high flex items-center justify-center text-on-surface-variant transition-colors relative"
            >
              <span className="material-symbols-outlined">notifications</span>
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
                    {decisions.map((d) => (
                      <tr key={d.id} className="hover:bg-surface-container-low transition-colors">
                        <td className="p-table-cell-padding font-code-sm text-code-sm text-tertiary">{d.resolution_id}</td>
                        <td className="p-table-cell-padding font-body-md text-body-md text-on-surface">{d.subject}</td>
                        <td className="p-table-cell-padding">{statusBadge(d.status)}</td>
                        <td className="p-table-cell-padding text-right font-code-sm text-code-sm text-on-surface">
                          {d.status === 'pending' ? 'N/A' : `${d.tally.yes} - ${d.tally.no} - ${d.tally.abstain}`}
                        </td>
                      </tr>
                    ))}
                    {decisions.length === 0 && (
                      <tr>
                        <td colSpan={4} className="p-table-cell-padding text-on-surface-variant font-body-md text-body-md">
                          No decisions recorded yet.
                        </td>
                      </tr>
                    )}
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
                {meetings.slice(0, 3).map((m) => {
                  const when = new Date(m.scheduled_at);
                  return (
                    <div key={m.id} className="flex gap-4 p-3 rounded-DEFAULT border border-outline-variant/50 bg-surface-container-lowest hover:border-primary/50 transition-colors cursor-pointer">
                      <div className="flex flex-col items-center justify-center w-12 h-12 bg-surface-container rounded-sm border border-outline-variant shrink-0">
                        <span className="font-label-bold text-label-bold uppercase text-error">{MONTHS[when.getMonth()]}</span>
                        <span className="font-headline-md text-headline-md font-bold text-on-surface leading-none">{when.getDate()}</span>
                      </div>
                      <div className="flex flex-col justify-center">
                        <h3 className="font-body-md text-body-md font-semibold text-on-surface line-clamp-1">{m.title}</h3>
                        <div className="flex items-center gap-1 text-on-surface-variant font-label-md text-label-md mt-1">
                          <span className="material-symbols-outlined text-[14px]">{m.meeting_type === 'virtual' ? 'videocam' : 'schedule'}</span>
                          <span>{when.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}{m.location ? ` • ${m.location}` : ''}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {meetings.length === 0 && (
                  <div className="text-on-surface-variant font-body-md text-body-md p-3">No upcoming meetings scheduled.</div>
                )}
              </div>
            </div>

            {/* Document Repository (Spans 6 columns) */}
            <div className="lg:col-span-6 bg-surface border border-outline-variant rounded-lg flex flex-col overflow-hidden">
              <div className="px-5 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">folder_special</span>
                  <h2 className="font-headline-sm text-headline-sm text-on-surface">Repository</h2>
                </div>
              </div>
              <div className="p-4 grid grid-cols-2 gap-3">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex items-center gap-3 p-3 rounded-DEFAULT border border-outline-variant hover:bg-surface-container-high transition-colors cursor-pointer group">
                    <span className="material-symbols-outlined text-tertiary text-[24px] group-hover:text-primary transition-colors">
                      {doc.file_type === 'xlsx' ? 'table_chart' : 'description'}
                    </span>
                    <div className="flex flex-col overflow-hidden">
                      <span className="font-body-md text-body-md text-on-surface truncate">{doc.title}</span>
                      <span className="font-label-md text-label-md text-on-surface-variant">
                        {(doc.file_size / 1024).toFixed(0)} KB · {new Date(doc.uploaded_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
                {documents.length === 0 && (
                  <div className="col-span-2 text-on-surface-variant font-body-md text-body-md p-3">No documents uploaded yet.</div>
                )}
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
                {members.map((mem) => (
                  <div key={mem.id} className="flex items-center justify-between p-2 rounded-DEFAULT hover:bg-surface-container transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center border border-outline-variant">
                        <span className="material-symbols-outlined text-on-primary-container icon-fill text-xl">person</span>
                      </div>
                      <div>
                        <div className="font-body-md text-body-md font-semibold text-on-surface">{mem.name}</div>
                        <div className="font-label-md text-label-md text-on-surface-variant capitalize">{mem.role.replace('_', ' ')}</div>
                      </div>
                    </div>
                    <a
                      href={`tel:${mem.phone}`}
                      className="w-8 h-8 rounded-DEFAULT bg-surface-container border border-outline-variant flex items-center justify-center text-on-surface-variant hover:text-primary hover:border-primary transition-colors"
                      title={mem.phone}
                    >
                      <span className="material-symbols-outlined text-[16px]">call</span>
                    </a>
                  </div>
                ))}
                {members.length === 0 && (
                  <div className="text-on-surface-variant font-body-md text-body-md p-2">No committee members added.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
