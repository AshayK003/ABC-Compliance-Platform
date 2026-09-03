/**
 * Shared authenticated fetch with automatic token refresh.
 *
 * On a 401 (except from auth endpoints themselves), tries POST /auth/refresh
 * once via the httpOnly refresh cookie, then retries the original request.
 * Concurrent 401s share a single in-flight refresh call. If refresh fails,
 * the original error is re-thrown and the caller logs the user out.
 */
import type { LoginResponse } from '../../types';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';

if (import.meta.env.PROD && !import.meta.env.VITE_API_URL) {
  // Misconfiguration alarm: a production bundle without VITE_API_URL talks
  // to a dev-only address. Loud on purpose — silent fallback hides outages.
  console.warn('VITE_API_URL is not set; API calls fall back to http://localhost:8000');
}

let authToken: string | null = null;
let refreshPromise: Promise<LoginResponse> | null = null;

export function setAuthToken(token: string | null | undefined) {
  authToken = token ?? null;
}

export function clearAuthToken() {
  authToken = null;
}

/** Refresh the access token using the refresh cookie. Deduplicated in-flight. */
export async function refreshAccessToken(): Promise<LoginResponse> {
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
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

// Endpoints that must never trigger a refresh-retry loop.
const NO_RETRY = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/me', '/auth/logout'];

export async function authenticatedFetch<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
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
      const err = new Error(error.detail || `HTTP ${response.status}`) as Error & { status?: number };
      err.status = response.status;
      throw err;
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  };

  try {
    return await makeRequest();
  } catch (err) {
    const is401 = err instanceof Error && (err as Error & { status?: number }).status === 401;
    if (!is401 || NO_RETRY.includes(endpoint)) {
      throw err;
    }
    try {
      const refreshResult = await refreshAccessToken();
      setAuthToken(refreshResult.access_token);
      return await makeRequest();
    } catch {
      setAuthToken(null);
      throw err;
    }
  }
}
