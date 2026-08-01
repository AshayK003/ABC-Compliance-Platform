import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { TokenPayload } from '../types';

interface AuthContextType {
  user: TokenPayload | null;
  login: (credentials: { phone: string; password: string }) => Promise<void>;
  register: (data: { name: string; phone: string; password: string; role: string; centreId?: string }) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  deleteAccount: () => Promise<void>;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

let accessToken: string | null = null;

function setAccessToken(token: string | null) {
  accessToken = token;
}

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include', // Include cookies for refresh token
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<TokenPayload | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check auth status on load
    fetchWithAuth<TokenPayload>('/auth/me')
      .then((userData) => {
        setUser(userData);
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const login = async (credentials: { phone: string; password: string }) => {
    const data = await fetchWithAuth<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    setAccessToken(data.access_token);

    // Fetch user after login
    const userData = await fetchWithAuth<TokenPayload>('/auth/me');
    setUser(userData);
  };

  const register = async (data: { name: string; phone: string; password: string; role: string; centreId?: string }) => {
    const res = await fetchWithAuth<{ access_token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        name: data.name,
        phone: data.phone,
        password: data.password,
        role: data.role,
        centre_id: data.centreId || null,
      }),
    });
    setAccessToken(res.access_token);

    // Fetch user after registration
    const userData = await fetchWithAuth<TokenPayload>('/auth/me');
    setUser(userData);
  };

  const refresh = async () => {
    const data = await fetchWithAuth<{ access_token: string }>('/auth/refresh', {
      method: 'POST',
    });
    setAccessToken(data.access_token);

    // Fetch user after refresh
    const userData = await fetchWithAuth<TokenPayload>('/auth/me');
    setUser(userData);
  };

  const logout = async () => {
    try {
      await fetchWithAuth('/auth/logout', {
        method: 'POST',
      });
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  };

  const deleteAccount = async () => {
    try {
      await fetchWithAuth('/auth/me', {
        method: 'DELETE',
      });
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        register,
        logout,
        refresh,
        deleteAccount,
        loading,
        isAuthenticated: !!user,
      }}
    >
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