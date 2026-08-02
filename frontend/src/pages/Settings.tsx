import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

interface UserSettings {
  emailNotifications: boolean;
  smsNotifications: boolean;
  pushNotifications: boolean;
  language: string;
  theme: 'light' | 'dark' | 'system';
  autoRefresh: boolean;
  refreshInterval: number;
}

const DEFAULT_SETTINGS: UserSettings = {
  emailNotifications: true,
  smsNotifications: false,
  pushNotifications: true,
  language: 'en',
  theme: 'system',
  autoRefresh: true,
  refreshInterval: 30,
};

export function Settings() {
  const { user } = useAuth();
  const { theme: contextTheme, setTheme } = useTheme();
  const [settings, setSettings] = useState<UserSettings>({
    ...DEFAULT_SETTINGS,
    theme: contextTheme, // Sync with actual theme from context
  });
  const [saved, setSaved] = useState(false);

  // Sync theme from context to settings
  const handleChange = (key: keyof UserSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setSaved(false);
    if (key === 'theme') {
      setTheme(value as 'light' | 'dark' | 'system');
    }
  };

  const handleSave = async () => {
    // In real app, call API to save settings
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Page Header */}
      <header className="bg-surface-container dark:bg-surface-container w-full sticky top-0 z-40 border-b border-outline-variant flex justify-between items-center h-16 px-gutter shrink-0">
              <h1 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Settings</h1>
              <button
                type="button"
                onClick={handleSave}
                disabled={saved}
                className="bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-primary-container disabled:opacity-50 flex items-center gap-2"
              >
                {saved ? (
                  <>
                    <span className="material-symbols-outlined text-[18px]">check</span>
                    <span>Saved</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">save</span>
                    <span>Save Changes</span>
                  </>
                )}
              </button>
            </header>

      <main className="flex-1 flex flex-col min-w-0 p-container-padding space-y-6">
        <div className="max-w-3xl mx-auto space-y-8">
          {/* Profile Section */}
          <section className="bg-surface-container-high border border-outline-variant rounded-lg p-6">
            <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">person</span>
              Profile
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                              <label className="block font-label-md text-label-md text-on-surface-variant mb-1" htmlFor="full-name">Full Name</label>
                              <input
                                id="full-name"
                                type="text"
                                value={user?.name || ''}
                                readOnly
                                className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md"
                              />
                            </div>
                            <div>
                              <label className="block font-label-md text-label-md text-on-surface-variant mb-1" htmlFor="role">Role</label>
                              <input
                                id="role"
                                type="text"
                                value={user?.role || ''}
                                readOnly
                                className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md"
                              />
                            </div>
                            <div>
                              <label className="block font-label-md text-label-md text-on-surface-variant mb-1" htmlFor="phone">Phone</label>
                              <input
                                id="phone"
                                type="tel"
                                value={user?.phone || ''}
                                readOnly
                                className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md"
                              />
                            </div>
                            <div>
                              <label className="block font-label-md text-label-md text-on-surface-variant mb-1" htmlFor="centre">Centre</label>
                              <input
                                id="centre"
                                type="text"
                                value={user?.centre_id ? `Centre ID: ${user.centre_id}` : 'Not assigned'}
                                readOnly
                                className="w-full bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md"
                              />
                            </div>
            </div>
          </section>

          {/* Notifications Preferences */}
          <section className="bg-surface-container-high border border-outline-variant rounded-lg p-6">
            <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">notifications</span>
              Notification Preferences
            </h2>
            <div className="space-y-4">
                          <label className="flex items-center justify-between cursor-pointer">
                            <div className="flex items-center gap-3">
                              <span className="material-symbols-outlined text-on-surface-variant">email</span>
                              <div>
                                <div className="font-medium text-on-surface">Email Notifications</div>
                                <div className="font-body-sm text-body-sm text-on-surface-variant">Receive email alerts for inspections, compliance, and fund updates</div>
                              </div>
                            </div>
                            <input
                                                            id="email-notifications"
                                                            type="checkbox"
                                                            checked={settings.emailNotifications}
                                                            onChange={(e) => handleChange('emailNotifications', e.target.checked)}
                                                            className="w-5 h-5 accent-primary"
                                                          />
                          </label>
                          <label className="flex items-center justify-between cursor-pointer">
                            <div className="flex items-center gap-3">
                              <span className="material-symbols-outlined text-on-surface-variant">sms</span>
                              <div>
                                <div className="font-medium text-on-surface">SMS Notifications</div>
                                <div className="font-body-sm text-body-sm text-on-surface-variant">Receive SMS alerts for critical compliance alerts only</div>
                              </div>
                            </div>
                            <input
                              id="sms-notifications"
                              type="checkbox"
                                                            checked={settings.smsNotifications}
                                                            onChange={(e) => handleChange('smsNotifications', e.target.checked)}
                                                            className="w-5 h-5 accent-primary"
                                                          />
                          </label>
                          <label className="flex items-center justify-between cursor-pointer">
                            <div className="flex items-center gap-3">
                              <span className="material-symbols-outlined text-on-surface-variant">notifications_active</span>
                              <div>
                                <div className="font-medium text-on-surface">Push Notifications</div>
                                <div className="font-body-sm text-body-sm text-on-surface-variant">Receive browser push notifications for real-time updates</div>
                              </div>
                            </div>
                            <input
                              id="push-notifications"
                              type="checkbox"
                                                            checked={settings.pushNotifications}
                                                            onChange={(e) => handleChange('pushNotifications', e.target.checked)}
                                                            className="w-5 h-5 accent-primary"
                                                          />
                          </label>
                        </div>
          </section>

          {/* Appearance */}
          <section className="bg-surface-container-high border border-outline-variant rounded-lg p-6">
            <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">palette</span>
              Appearance
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block font-label-md text-label-md text-on-surface-variant mb-2">Theme</label>
                <div className="flex gap-4">
                  {['light', 'dark', 'system'].map((theme) => (
                    <label key={theme} className={`flex-1 flex flex-col items-center p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                      settings.theme === theme
                        ? 'border-primary bg-primary-container/20'
                        : 'border-outline-variant hover:border-primary/50'
                    }`}>
                      <input
                        type="radio"
                        name="theme"
                        value={theme}
                        checked={theme === settings.theme}
                        onChange={(e) => handleChange('theme', e.target.value as 'light' | 'dark' | 'system')}
                        className="sr-only"
                      />
                      <span className="material-symbols-outlined text-4xl text-on-surface-variant mb-2">
                        {theme === 'light' ? 'light_mode' : theme === 'dark' ? 'dark_mode' : 'settings_brightness'}
                      </span>
                      <span className="font-label-bold text-label-bold text-on-surface capitalize">{theme}</span>
                    </label>
                  ))})
                </div>
              </div>
              <div>
                <label className="block font-label-md text-label-md text-on-surface-variant mb-2">Language</label>
                <select
                  value={settings.language}
                  onChange={(e) => handleChange('language', e.target.value)}
                  className="w-full md:w-1/3 bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                >
                  <option value="en">English</option>
                  <option value="hi">हिंदी</option>
                  <option value="kn">ಕನ್ನಡ</option>
                  <option value="ta">தமிழ்</option>
                  <option value="te">తెలుగు</option>
                </select>
              </div>
            </div>
          </section>

          {/* Data & Sync */}
          <section className="bg-surface-container-high border border-outline-variant rounded-lg p-6">
            <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">sync</span>
              Data & Sync
            </h2>
            <div className="space-y-4">
              <label className="flex items-center justify-between cursor-pointer">
                              <div className="flex items-center gap-3">
                                <span className="material-symbols-outlined text-on-surface-variant">refresh</span>
                                <div>
                                  <div className="font-medium text-on-surface">Auto Refresh</div>
                                  <div className="font-body-sm text-body-sm text-on-surface-variant">Automatically refresh data on all pages</div>
                                </div>
                              </div>
                              <input
                                id="auto-refresh"
                                type="checkbox"
                                checked={settings.autoRefresh}
                                onChange={(e) => handleChange('autoRefresh', e.target.checked)}
                                className="w-5 h-5 accent-primary"
                              />
                            </label>
              <div>
                              <label className="block font-label-md text-label-md text-on-surface-variant mb-2" htmlFor="refresh-interval">Refresh Interval (seconds)</label>
                              <select
                                                                                            id="refresh-interval"
                                                                                            value={settings.refreshInterval}
                                                                                            onChange={(e) => handleChange('refreshInterval', Number.parseInt(e.target.value))}
                                                                                            disabled={!settings.autoRefresh}
                                                                                            className="w-full md:w-1/3 bg-background border border-outline-variant rounded px-3 py-2 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                                                                                          >
                  <option value={15}>15 seconds</option>
                  <option value={30}>30 seconds</option>
                  <option value={60}>1 minute</option>
                  <option value={120}>2 minutes</option>
                  <option value={300}>5 minutes</option>
                </select>
              </div>
            </div>
          </section>

          {/* Danger Zone */}
          <section className="bg-surface-container-high border border-error/30 rounded-lg p-6">
            <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-error">warning</span>
              Danger Zone
            </h2>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-error">Delete Account</div>
                <div className="font-body-sm text-body-sm text-on-surface-variant">Permanently delete your account and all associated data. This action cannot be undone.</div>
              </div>
              <button
                type="button"
                className="bg-error-container text-on-error-container font-label-bold text-label-bold px-4 py-2 rounded transition-colors hover:bg-error/20"
              >
                <span className="material-symbols-outlined text-[18px] mr-2">delete_forever</span>
                Delete Account
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}