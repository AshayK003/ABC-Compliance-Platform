import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, loading } = useAuth();
  const [formData, setFormData] = useState({ phone: '', password: '' });
  const [error, setError] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [registerData, setRegisterData] = useState({ name: '', phone: '', password: '', role: 'vet', centreId: '' });

  const from = (location.state as { from?: Location })?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (isRegister) {
        await register(registerData);
      } else {
        await login(formData);
      }
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    }
  };

  const handleSwitch = () => {
    setIsRegister(!isRegister);
    setError('');
  };

  if (!isRegister) {
    return (
      <div className="flex h-screen items-center justify-center bg-background p-4">
        <div className="w-full max-w-md bg-surface-container-high border border-outline-variant rounded-lg p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4">
              <span className="material-symbols-outlined text-primary text-4xl">policy</span>
            </div>
            <h1 className="text-headline-md font-headline-md font-bold text-on-surface">ABC Digital Compliance</h1>
            <p className="text-body-sm text-body-sm text-on-surface-variant mt-2">Sign in to continue</p>
          </div>

          {error && (
            <div className="mb-6 p-3 bg-error-container/20 border border-error/30 rounded text-error text-body-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="phone" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                Phone Number
              </label>
              <input
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
                placeholder="Enter phone number"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
                placeholder="Enter password"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2.5 rounded transition-colors hover:bg-primary-container disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-on-primary/30 border-t-on-primary"></div>
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="mt-6 text-center font-body-sm text-body-sm text-on-surface-variant">
            Don't have an account?{' '}
            <button
              type="button"
              onClick={handleSwitch}
              className="text-primary hover:text-primary-container font-medium underline"
            >
              Register
            </button>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md bg-surface-container-high border border-outline-variant rounded-lg p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4">
            <span className="material-symbols-outlined text-primary text-4xl">policy</span>
          </div>
          <h1 className="text-headline-md font-headline-md font-bold text-on-surface">Register Centre</h1>
          <p className="text-body-sm text-body-sm text-on-surface-variant mt-2">Create a new ABC centre account</p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-error-container/20 border border-error/30 rounded text-error text-body-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
              Centre Name
            </label>
            <input
              id="name"
              type="text"
              value={registerData.name}
              onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
              placeholder="Enter centre name"
              required
            />
          </div>

          <div>
            <label htmlFor="reg-phone" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
              Phone Number
            </label>
            <input
              id="reg-phone"
              type="tel"
              value={registerData.phone}
              onChange={(e) => setRegisterData({ ...registerData, phone: e.target.value })}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
              placeholder="Enter phone number"
              required
            />
          </div>

          <div>
            <label htmlFor="reg-password" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
              Password
            </label>
            <input
              id="reg-password"
              type="password"
              value={registerData.password}
              onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
              placeholder="Enter password"
              required
            />
          </div>

          <div>
            <label htmlFor="role" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
              Role
            </label>
            <select
              id="role"
              value={registerData.role}
              onChange={(e) => setRegisterData({ ...registerData, role: e.target.value })}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none cursor-pointer"
            >
              <option value="vet">Veterinarian</option>
              <option value="surgeon">Surgeon</option>
              <option value="admin">Administrator</option>
            </select>
          </div>

          <div>
            <label htmlFor="centreId" className="block font-label-md text-label-md text-on-surface-variant mb-1.5">
              Centre ID (optional)
            </label>
            <input
              id="centreId"
              type="text"
              value={registerData.centreId}
              onChange={(e) => setRegisterData({ ...registerData, centreId: e.target.value })}
              className="w-full bg-background border border-outline-variant rounded px-3 py-2.5 text-on-surface font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
              placeholder="Enter centre ID if known"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2.5 rounded transition-colors hover:bg-primary-container disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-on-primary/30 border-t-on-primary"></div>
                Creating account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <p className="mt-6 text-center font-body-sm text-body-sm text-on-surface-variant">
          Already have an account?{' '}
          <button
            type="button"
            onClick={handleSwitch}
            className="text-primary hover:text-primary-container font-medium underline"
          >
            Sign In
          </button>
        </p>
      </div>
    </div>
  );
}