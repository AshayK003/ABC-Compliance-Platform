import type { User, LoginResponse, RegisterResponse } from '../../types';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';

let authToken: string | null = null;
let refreshPromise: Promise<LoginResponse> | null = null;

export function setAuthToken(token: string | null | undefined) {
  authToken = token ?? null;
}

async function refreshAccessToken(): Promise<LoginResponse> {
  if (refreshPromise) {
    return refreshPromise;
  }
  
  refreshPromise = (async () => {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Refresh failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return response.json();
  })();
  
  try {
    const result = await refreshPromise;
    return result;
  } finally {
    refreshPromise = null;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const makeRequest = async (): Promise<T> => {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  };

  try {
    return await makeRequest();
  } catch (err) {
    // If 401 and not already trying to refresh, attempt refresh
    if (err instanceof Error && err.message.startsWith('HTTP 401') && endpoint !== '/auth/refresh' && endpoint !== '/auth/login' && endpoint !== '/auth/register') {
      try {
        const refreshResult = await refreshAccessToken();
        setAuthToken(refreshResult.access_token);
        // Retry the original request
        return await makeRequest();
      } catch {
        // Refresh failed, clear token and re-throw original error
        setAuthToken(null);
        throw err;
      }
    }
    throw err;
  }
}

export const authApi = {
  login: (phone: string, password: string) =>
    request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
    }),

  register: (data: { name: string; phone: string; password: string; centre_id?: string }) =>
    request<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMe: () => request<User>('/auth/me'),
  refresh: () => request<LoginResponse>('/auth/refresh', { method: 'POST' }),
  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),
  deleteAccount: () => request<{ message: string }>('/auth/me', { method: 'DELETE' }),
};