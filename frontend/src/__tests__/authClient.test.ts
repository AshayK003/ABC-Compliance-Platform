import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock fetch globally
const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

// Use fake timers not required; we test logic directly.
import { authenticatedFetch, setAuthToken, clearAuthToken } from '../services/api/client';

function jsonResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

describe('authenticatedFetch 401 → refresh → retry', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    setAuthToken('stale-token');
  });

  afterEach(() => {
    clearAuthToken();
  });

  it('retries with a fresh token after a successful refresh', async () => {
    // Call 1: original request → 401
    // Call 2: /auth/refresh → 200 with new token
    // Call 3: retried original → 200
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Not authenticated' }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: 'fresh-token', token_type: 'bearer' }))
      .mockResolvedValueOnce(jsonResponse(200, { data: 'payload' }));

    const result = await authenticatedFetch<{ data: string }>('/centres');

    expect(result).toEqual({ data: 'payload' });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    // Refresh call must hit the refresh endpoint with the cookie
    expect(fetchMock.mock.calls[1][0]).toContain('/auth/refresh');
    // Retried request carries the new bearer token
    const retryHeaders = fetchMock.mock.calls[2][1].headers;
    expect(retryHeaders.Authorization).toBe('Bearer fresh-token');
  });

  it('throws the original error when refresh also fails', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Not authenticated' }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'No refresh token' }));

    await expect(authenticatedFetch('/centres')).rejects.toThrow('Not authenticated');
    expect(fetchMock).toHaveBeenCalledTimes(2); // no retry after failed refresh
  });

  it('does not attempt refresh for login/register/refresh endpoints', async () => {
    fetchMock.mockResolvedValue(jsonResponse(401, { detail: 'Invalid credentials' }));

    await expect(authenticatedFetch('/auth/login', { method: 'POST', body: '{}' })).rejects.toThrow();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('deduplicates concurrent refresh calls', async () => {
    // Two requests 401 at the same time; refresh must only fire once.
    let refreshCalls = 0;
    const expired = new Set(['/centres', '/dogs']);
    fetchMock.mockImplementation(async (url: string) => {
      if (String(url).includes('/auth/refresh')) {
        refreshCalls += 1;
        return jsonResponse(200, { access_token: 'shared-fresh', token_type: 'bearer' });
      }
      // Each endpoint 401s on its first attempt, succeeds on retry.
      for (const ep of ['/centres', '/dogs']) {
        if (String(url).includes(ep)) {
          if (expired.has(ep)) {
            expired.delete(ep);
            return jsonResponse(401, { detail: 'expired' });
          }
          return jsonResponse(200, { ok: true });
        }
      }
      return jsonResponse(404, { detail: 'not found' });
    });

    const [a, b] = await Promise.all([
      authenticatedFetch('/centres'),
      authenticatedFetch('/dogs'),
    ]);

    expect(a).toEqual({ ok: true });
    expect(b).toEqual({ ok: true });
    expect(refreshCalls).toBe(1); // shared, not duplicated
  });

  it('non-401 errors pass through untouched', async () => {
    fetchMock.mockResolvedValue(jsonResponse(500, { detail: 'Server error' }));

    await expect(authenticatedFetch('/centres')).rejects.toThrow('Server error');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
