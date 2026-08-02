import type { Centre } from '../../types';

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

export interface CentresResponse {
  data: Centre[];
  total: number;
  page: number;
  pageSize: number;
}

export const centresApi = {
  getCentres: (params?: { limit?: number; offset?: number; search?: string; district?: string; status?: string }) => {
    const search = new URLSearchParams();
    if (params?.limit) search.set('limit', String(params.limit));
    if (params?.offset) search.set('offset', String(params.offset));
    if (params?.search) search.set('search', params.search);
    if (params?.district) search.set('district', params.district);
    if (params?.status) search.set('status', params.status);
    const query = search.toString() ? `?${search}` : '';
    return request<Centre[] | CentresResponse>(`/centres${query}`);
  },
  getCentre: (id: string) => request<Centre>(`/centres/${id}`),
  createCentre: (data: { name: string; code: string; district: string; state: string; capacity?: number }) =>
    request<Centre>('/centres', { method: 'POST', body: JSON.stringify(data) }),
  getCentreStaff: (centreId: string) => request<Array<{ id: string; name: string; role: string; phone: string }>>(`/centres/${centreId}/staff`),
};