import { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import type { TokenPayload } from '../types';
import { setAuthToken } from '../services/api';
import { authApi } from '../services/api/auth';

interface AuthContextType {
  user: TokenPayload | null;
  login: (credentials: { phone: string; password: string }) => Promise<void>;
  register: (data: { name: string; phone: string; password: string; centreId?: string }) => Promise<void>;
  logout: () => Promise<void>;
  deleteAccount: () => Promise<void>;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { readonly children: React.ReactNode }) {
  const [user, setUser] = useState<TokenPayload | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const userData = await authApi.getMe();
      setUser(userData);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    // Check auth status on load
    fetchUser().finally(() => {
      setLoading(false);
    });
  }, [fetchUser]);

  const login = async (credentials: { phone: string; password: string }) => {
    const data = await authApi.login(credentials.phone, credentials.password);
    setAuthToken(data.access_token);
    await fetchUser();
  };

  const register = async (data: { name: string; phone: string; password: string; centreId?: string }) => {
    const res = await authApi.register({
      name: data.name,
      phone: data.phone,
      password: data.password,
      centre_id: data.centreId,
    });
    setAuthToken(res.access_token);
    await fetchUser();
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      setAuthToken(null);
      setUser(null);
    }
  };

  const deleteAccount = async () => {
    try {
      await authApi.deleteAccount();
    } finally {
      setAuthToken(null);
      setUser(null);
    }
  };

  const authValue = useMemo(
    () => ({
      user,
      login,
      register,
      logout,
      deleteAccount,
      loading,
      isAuthenticated: !!user,
    }),
    [user, login, register, logout, deleteAccount, loading]
  );

  return (
    <AuthContext.Provider value={authValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}