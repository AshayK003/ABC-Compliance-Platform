import { useState } from 'react';
import { DataTable } from '../components/DataTable';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  read: boolean;
  created_at: string;
}

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: '1',
    title: 'New Inspection Scheduled',
    message: 'Surprise inspection scheduled for BBMP Centre 1 on Aug 5, 2026',
    type: 'info',
    read: false,
    created_at: '2026-08-01T10:30:00Z',
  },
  {
    id: '2',
    title: 'Fund Disbursement Complete',
    message: '₹1.5L disbursed to BBMP Centre 1 for Sterilization programme Q2',
    type: 'success',
    read: false,
    created_at: '2026-07-30T14:20:00Z',
  },
  {
    id: '3',
    title: 'Compliance Alert',
    message: 'BBMP Centre 2 compliance score dropped below 90%',
    type: 'warning',
    read: true,
    created_at: '2026-07-28T09:15:00Z',
  },
  {
    id: '4',
    title: 'Surgery Log Submitted',
    message: '4 surgeries recorded at Test Centre today',
    type: 'info',
    read: true,
    created_at: '2026-07-27T16:45:00Z',
  },
];

export function Notifications() {
  const [notifications] = useState<Notification[]>(MOCK_NOTIFICATIONS);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const filtered = filter === 'unread' ? notifications.filter(n => !n.read) : notifications;
  const unreadCount = notifications.filter(n => !n.read).length;

  const handleMarkAllRead = () => {
    // In real app, call API to mark all as read
    notifications.forEach(n => n.read = true);
  };

  const typeColors = {
    info: 'bg-primary/10 text-primary border-primary/20',
    success: 'bg-secondary-container/20 text-secondary-container border-secondary-container/30',
    warning: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    error: 'bg-error-container/20 text-error-container border-error-container/30',
  };

  const typeIcons = {
    info: 'info',
    success: 'check_circle',
    warning: 'warning',
    error: 'error',
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Page Header */}
      <header className="bg-surface-container dark:bg-surface-container w-full sticky top-0 z-40 border-b border-outline-variant flex justify-between items-center h-16 px-gutter shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Notifications</h1>
          {unreadCount > 0 && (
            <span className="bg-error/10 text-error font-label-bold text-label-sm px-2 py-0.5 rounded-full">
              {unreadCount} unread
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as 'all' | 'unread')}
            className="bg-background border border-outline-variant rounded pl-3 pr-8 py-2 text-on-surface font-body-sm text-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none cursor-pointer"
          >
            <option value="all">All</option>
            <option value="unread">Unread Only</option>
          </select>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="bg-primary text-on-primary font-label-bold text-label-sm px-3 py-2 rounded transition-colors hover:bg-primary-container flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[16px]">done_all</span>
              Mark All Read
            </button>
          )}
        </div>
      </header>

      <main className="flex-1 flex flex-col min-w-0 p-container-padding space-y-6">
        {filtered.length === 0 ? (
          <div className="flex-1 flex items-center justify-center bg-background">
            <div className="text-center p-8 fade-in">
              <span className="material-symbols-outlined text-6xl text-on-surface-variant mb-4 block">notifications_none</span>
              <h3 className="font-headline-sm text-headline-sm text-on-surface mb-2">
                {filter === 'unread' ? 'No Unread Notifications' : 'No Notifications Yet'}
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant">
                {filter === 'unread' ? 'All caught up!' : 'Notifications will appear here when you receive alerts, updates, or reminders.'}
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-surface-container-high border border-outline-variant rounded overflow-hidden flex-1 flex flex-col">
            <div className="overflow-x-auto">
              <DataTable
                data={filtered}
                columns={[
                  {
                    key: 'type',
                    header: '',
                    width: '48px',
                    align: 'center',
                    render: (n: Notification) => (
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${typeColors[n.type]}`}>
                        <span className="material-symbols-outlined text-[18px]">{typeIcons[n.type]}</span>
                      </span>
                    ),
                  },
                  {
                    key: 'title',
                    header: 'Title',
                    render: (n: Notification) => (
                      <div>
                        <div className={`font-medium text-on-surface ${!n.read ? 'font-bold' : ''}`}>{n.title}</div>
                        <div className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">{n.message}</div>
                      </div>
                    ),
                  },
                  {
                    key: 'created_at',
                    header: 'Time',
                    width: '180px',
                    render: (n: Notification) => (
                      <div className="font-body-sm text-body-sm text-on-surface-variant">
                        {new Date(n.created_at).toLocaleString()}
                      </div>
                    ),
                  },
                  {
                    key: 'read',
                    header: 'Status',
                    width: '100px',
                    align: 'center',
                    render: (n: Notification) => (
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold tracking-wide uppercase ${n.read ? 'bg-primary-container/10 text-primary border border-primary/20' : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'}`}>
                        {n.read ? 'Read' : 'Unread'}
                      </span>
                    ),
                  },
                  {
                    key: 'actions',
                    header: '',
                    width: '48px',
                    align: 'center',
                    render: (n: Notification) => (
                      <button
                        className="text-on-surface-variant hover:text-primary p-1 rounded transition-colors"
                        aria-label={n.read ? 'Mark as unread' : 'Mark as read'}
                      >
                        <span className="material-symbols-outlined text-[20px]">
                          {n.read ? 'mark_email_unread' : 'mark_email_read'}
                        </span>
                      </button>
                    ),
                  },
                ]}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}