import type { Surgery } from '../../types';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
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

export const surgeriesApi = {
  getSurgeries: (params?: { centre_id?: string; dog_id?: string; from_date?: string; to_date?: string; limit?: number; offset?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<Surgery[]>(`/surgeries${query}`);
  },
  getSurgery: (id: string) => request<Surgery>(`/surgeries/${id}`),
  createSurgery: (data: { dog_id: string; centre_id: string; staff_id: string; surgery_type: string; weight?: number; complications?: string; timestamp?: string }) =>
    request<Surgery>('/surgeries', { method: 'POST', body: JSON.stringify(data) }),
};