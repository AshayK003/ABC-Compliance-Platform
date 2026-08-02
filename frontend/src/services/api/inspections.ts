import type { Inspection } from '../../types';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';

let authToken: string | null = null;

export function setAuthToken(token: string | null | undefined) {
  authToken = token ?? null;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
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
}

export const inspectionsApi = {
  getInspections: (params?: { centre_id?: string; status?: string; limit?: number; offset?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<Inspection[]>(`/inspections${query}`);
  },
  getInspection: (id: string) => request<Inspection>(`/inspections/${id}`),
  createInspection: (data: { centre_id: string; inspector_id: string; scheduled_at?: string; status?: string }) =>
    request<Inspection>('/inspections', { method: 'POST', body: JSON.stringify(data) }),
};