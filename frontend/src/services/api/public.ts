import type { Complaint, SyncQueueItem } from '../../types';

interface HeatmapState {
  state: string;
  centres: number;
  inspections: number;
  compliance_rate: number;
  risk: 'critical' | 'moderate' | 'compliant';
}

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

export const publicApi = {
  // Complaints
  getComplaints: (params?: { centre_id?: string; status?: string; limit?: number; offset?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<Complaint[]>(`/public/complaints${query}`);
  },
  getComplaint: (id: string) => request<Complaint>(`/public/complaints/${id}`),
  createComplaint: (data: { centre_id: string; citizen_phone: string; description: string }) =>
    request<Complaint>('/public/complaints', { method: 'POST', body: JSON.stringify(data) }),
  updateComplaint: (id: string, data: { status: string; resolution?: string }) =>
    request<Complaint>(`/public/complaints/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Sync Queue
  enqueueSync: (data: { entity_type: string; entity_id: string; operation: string; payload: Record<string, unknown>; idempotency_key: string }) =>
    request<SyncQueueItem>('/sync/enqueue', { method: 'POST', body: JSON.stringify(data) }),
  getPendingSync: (params?: { entity_type?: string; limit?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<SyncQueueItem[]>(`/sync/pending${query}`);
  },
  markSynced: (id: string) => request<SyncQueueItem>(`/sync/mark-synced/${id}`, { method: 'POST' }),
  markFailed: (id: string, error: string) => request<SyncQueueItem>(`/sync/mark-failed/${id}`, { method: 'POST', body: JSON.stringify({ error }) }),
  retryFailed: (max_retries?: number) => request<{ retried: number }>('/sync/retry-failed', { method: 'POST', body: JSON.stringify({ max_retries }) }),
  getSyncStatus: (idempotency_key: string) => request<SyncQueueItem>(`/sync/status/${idempotency_key}`),

  // Heatmap
  getHeatmap: () => request<HeatmapState[]>('/public/heatmap'),
};