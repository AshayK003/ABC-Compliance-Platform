import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

function getRoleIcon(role?: string): string {
  if (role === 'admin') return 'admin_panel_settings';
  if (role === 'surgeon') return 'medical_services';
  return 'pets';
}

export function Profile() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'activity'>('profile');

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Page Header */}
      <header className="bg-surface-container dark:bg-surface-container w-full sticky top-0 z-40 border-b border-outline-variant flex justify-between items-center h-16 px-gutter shrink-0">
        <h1 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Profile</h1>
      </header>

      <main className="flex-1 flex flex-col min-w-0 p-container-padding space-y-6">
        <div className="max-w-4xl mx-auto">
          {/* Profile Header Card */}
          <section className="bg-surface-container-high border border-outline-variant rounded-lg overflow-hidden">
            <div className="p-6 md:p-8 bg-primary/5">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div className="flex items-center gap-4">
                  <div className="w-24 h-24 rounded-full bg-primary-container flex items-center justify-center">
                    <span className="material-symbols-outlined text-4xl text-on-primary-container">
                      {getRoleIcon(user?.role)}
                    </span>
                  </div>
                  <div>
                    <h2 className="font-display-md text-display-md font-bold text-on-surface">{user?.name || 'User'}</h2>
                    <div className="flex items-center gap-3 mt-1 text-on-surface-variant">
                      <span className="font-label-md text-label-md capitalize">{user?.role}</span>
                      <span className="w-1 h-1 rounded-full bg-primary"></span>
                      <span className="font-label-md text-label-md">{user?.phone}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                                  <button type="button" className="bg-surface-container-high border border-outline-variant text-on-surface font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-surface-variant flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[18px]">edit</span>
                                    Edit Profile
                                  </button>
                                  <button type="button" className="bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-primary-container flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[18px]">security</span>
                                    Security
                                  </button>
                                </div>
              </div>
            </div>
          </section>

          {/* Tab Navigation */}
          <nav className="flex gap-1 bg-surface-container-high border border-outline-variant rounded-lg p-1" role="tablist">
            {[
              { id: 'profile', label: 'Profile', icon: 'person' },
              { id: 'security', label: 'Security', icon: 'security' },
              { id: 'activity', label: 'Activity', icon: 'history' },
            ].map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-md font-label-md text-label-md transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary text-on-primary shadow-sm'
                    : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>

          {/* Tab Content */}
          <div className="bg-surface-container-high border border-outline-variant rounded-lg rounded-t-none p-6">
            {activeTab === 'profile' && (
              <div className="space-y-6 max-w-2xl">
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Personal Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Full Name</label>
                    <input type="text" value={user?.name || ''} readOnly className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md" />
                  </div>
                  <div>
                    <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Phone Number</label>
                    <input type="tel" value={user?.phone || ''} readOnly className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md" />
                  </div>
                  <div>
                    <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Role</label>
                    <input type="text" value={user?.role || ''} readOnly className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md" />
                  </div>
                  <div>
                    <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Centre</label>
                    <input type="text" value={user?.centre_id ? `Centre ID: ${user.centre_id}` : 'Not assigned'} readOnly className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md" />
                  </div>
                </div>
                <div className="flex gap-2">
                                  <button type="button" className="bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-primary-container flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[18px]">edit</span>
                                    Edit Profile
                                  </button>
                                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6 max-w-2xl">
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Password & Security</h3>
                <div className="bg-surface-container border border-outline-variant rounded-lg p-6 space-y-4">
                  <div className="flex items-center justify-between">
                                      <div>
                                        <h4 className="font-medium text-on-surface">Change Password</h4>
                                        <p className="font-body-sm text-body-sm text-on-surface-variant">Update your password to keep your account secure</p>
                                      </div>
                                      <button type="button" className="bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-primary-container flex items-center gap-2">
                                        <span className="material-symbols-outlined text-[18px]">key</span>
                                        Change Password
                                      </button>
                                    </div>
                  <div className="flex items-center justify-between border-t border-outline-variant pt-4">
                                      <div>
                                        <h4 className="font-medium text-on-surface">Two-Factor Authentication</h4>
                                        <p className="font-body-sm text-body-sm text-on-surface-variant">Add an extra layer of security to your account</p>
                                      </div>
                                      <button type="button" className="bg-surface-container-high border border-outline-variant text-on-surface font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-surface-variant flex items-center gap-2">
                                        <span className="material-symbols-outlined text-[18px]">shield</span>
                                        Enable 2FA
                                      </button>
                                    </div>
                                    <div className="flex items-center justify-between border-t border-outline-variant pt-4">
                                      <div>
                                        <h4 className="font-medium text-on-surface">Active Sessions</h4>
                                        <p className="font-body-sm text-body-sm text-on-surface-variant">Manage devices logged into your account</p>
                                      </div>
                                      <button type="button" className="bg-surface-container-high border border-outline-variant text-on-surface font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-surface-variant flex items-center gap-2">
                                        <span className="material-symbols-outlined text-[18px]">devices</span>
                                        Manage Sessions
                                      </button>
                                    </div>
                </div>
              </div>
            )}

            {activeTab === 'activity' && (
              <div className="space-y-6 max-w-2xl">
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Recent Activity</h3>
                <div className="bg-surface-container border border-outline-variant rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-bold text-label-bold uppercase tracking-wider">
                        <th className="p-4 text-left">Action</th>
                        <th className="p-4 text-left">Details</th>
                        <th className="p-4 text-left">Time</th>
                        <th className="p-4 text-left">IP Address</th>
                      </tr>
                    </thead>
                    <tbody className="text-body-md">
                      <tr className="border-t border-outline-variant/50 hover:bg-surface-variant/30">
                        <td className="p-4 font-medium text-on-surface">Login</td>
                        <td className="p-4 text-on-surface-variant">Successful login from dashboard</td>
                        <td className="p-4 text-on-surface-variant">Aug 1, 2026, 10:30 AM</td>
                        <td className="p-4 font-code-sm text-tertiary">192.168.1.100</td>
                      </tr>
                      <tr className="border-t border-outline-variant/50 hover:bg-surface-variant/30">
                        <td className="p-4 font-medium text-on-surface">Surgery Logged</td>
                        <td className="p-4 text-on-surface-variant">Spay (OVH) at BBMP Centre 1</td>
                        <td className="p-4 text-on-surface-variant">Aug 1, 2026, 10:35 AM</td>
                        <td className="p-4 font-code-sm text-tertiary">192.168.1.100</td>
                      </tr>
                      <tr className="border-t border-outline-variant/50 hover:bg-surface-variant/30">
                        <td className="p-4 font-medium text-on-surface">Inspection Scheduled</td>
                        <td className="p-4 text-on-surface-variant">BBMP Centre 2 - Aug 5, 2026</td>
                        <td className="p-4 text-on-surface-variant">Jul 31, 2026, 2:15 PM</td>
                        <td className="p-4 font-code-sm text-tertiary">192.168.1.100</td>
                      </tr>
                      <tr className="border-t border-outline-variant/50 hover:bg-surface-variant/30">
                        <td className="p-4 font-medium text-on-surface">Fund Allocation</td>
                        <td className="p-4 text-on-surface-variant">₹1.5L to BBMP Centre 1</td>
                        <td className="p-4 text-on-surface-variant">Jul 30, 2026, 11:20 AM</td>
                        <td className="p-4 font-code-sm text-tertiary">192.168.1.100</td>
                      </tr>
                      <tr className="border-t border-outline-variant/50 hover:bg-surface-variant/30">
                        <td className="p-4 font-medium text-on-surface">Password Changed</td>
                        <td className="p-4 text-on-surface-variant">Password updated successfully</td>
                        <td className="p-4 text-on-surface-variant">Jul 28, 2026, 9:45 AM</td>
                        <td className="p-4 font-code-sm text-tertiary">192.168.1.100</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}