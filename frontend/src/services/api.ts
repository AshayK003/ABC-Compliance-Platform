import type { Centre, Dog, Surgery, Inspection, Grant, Allocation, Expense, Complaint, SyncQueueItem } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('auth_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  // Auth
  login: (phone: string, password: string) =>
    request<{ access_token: string; token_type: string; user_id: string; role: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
    }),

  register: (data: { name: string; phone: string; password: string; role: string; centre_id?: string }) =>
    request<{ id: string; name: string; role: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMe: () => request<{ user_id: string; role: string }>('/auth/me'),

  // Centres
  getCentres: () => request<Centre[]>('/centres'),
  getCentre: (id: string) => request<Centre>(`/centres/${id}`),
  createCentre: (data: { name: string; code: string; district: string; state: string; capacity?: number }) =>
    request<Centre>('/centres', { method: 'POST', body: JSON.stringify(data) }),

  // Dogs
  getDogs: (params?: { centre_id?: string; status?: string }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    return request<Dog[]>(`/dogs?${search}`);
  },
  getDog: (id: string) => request<Dog>(`/dogs/${id}`),
  createDog: (data: { centre_id: string; tag_id: string; sex: string; age_estimate?: number; weight?: number; status?: string }) =>
    request<Dog>('/dogs', { method: 'POST', body: JSON.stringify(data) }),

  // Surgeries
  getSurgeries: (params?: { centre_id?: string; dog_id?: string; from_date?: string; to_date?: string }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    return request<Surgery[]>(`/surgeries?${search}`);
  },
  getSurgery: (id: string) => request<Surgery>(`/surgeries/${id}`),
  createSurgery: (data: { dog_id: string; centre_id: string; staff_id: string; surgery_type: string; weight?: number; complications?: string; timestamp?: string }) =>
    request<Surgery>('/surgeries', { method: 'POST', body: JSON.stringify(data) }),

  // Inspections
  getInspections: (params?: { centre_id?: string; status?: string }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    return request<Inspection[]>(`/inspections?${search}`);
  },
  getInspection: (id: string) => request<Inspection>(`/inspections/${id}`),
  createInspection: (data: { centre_id: string; inspector_id: string; scheduled_at?: string; status?: string }) =>
    request<Inspection>('/inspections', { method: 'POST', body: JSON.stringify(data) }),

  // Grants
  getGrants: () => request<Grant[]>('/grants'),
  getGrant: (id: string) => request<Grant>(`/grants/${id}`),
  createGrant: (data: { awbi_ref: string; amount: number; purpose: string; financial_year: string; status?: string }) =>
    request<Grant>('/grants', { method: 'POST', body: JSON.stringify(data) }),

  // Allocations
  getAllocations: (params?: { grant_id?: string; centre_id?: string }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    return request<Allocation[]>(`/allocations?${search}`);
  },
  createAllocation: (data: { grant_id: string; centre_id: string; amount: number }) =>
    request<Allocation>('/allocations', { method: 'POST', body: JSON.stringify(data) }),

  // Expenses
  getExpenses: (params?: { allocation_id?: string }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    return request<Expense[]>(`/expenses?${search}`);
  },
  createExpense: (data: { allocation_id: string; surgery_id?: string; category: string; amount: number; bill_ref?: string; expense_at?: string }) =>
    request<Expense>('/expenses', { method: 'POST', body: JSON.stringify(data) }),

  // Complaints
  getComplaints: (params?: { centre_id?: string; status?: string }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    return request<Complaint[]>(`/public/complaints?${search}`);
  },
  createComplaint: (data: { centre_id: string; citizen_phone: string; description: string }) =>
    request<Complaint>('/public/complaints', { method: 'POST', body: JSON.stringify(data) }),
  updateComplaint: (id: string, data: { status: string; resolution?: string }) =>
    request<Complaint>(`/public/complaints/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Sync Queue
  enqueueSync: (data: { entity_type: string; entity_id: string; operation: string; payload: Record<string, unknown>; idempotency_key: string }) =>
    request<SyncQueueItem>('/sync/enqueue', { method: 'POST', body: JSON.stringify(data) }),
  getPendingSync: (params?: { entity_type?: string; limit?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    return request<SyncQueueItem[]>(`/sync/pending?${search}`);
  },
  markSynced: (id: string) => request<SyncQueueItem>(`/sync/mark-synced/${id}`, { method: 'POST' }),
  markFailed: (id: string, error: string) => request<SyncQueueItem>(`/sync/mark-failed/${id}`, { method: 'POST', body: JSON.stringify({ error }) }),
  retryFailed: (max_retries?: number) => request<{ retried: number }>('/sync/retry-failed', { method: 'POST', body: JSON.stringify({ max_retries }) }),
  getSyncStatus: (idempotency_key: string) => request<SyncQueueItem>(`/sync/status/${idempotency_key}`),
};

// Re-export types
export type { Centre, Dog, Surgery, Inspection, Grant, Allocation, Expense, Complaint, SyncQueueItem } from '../types';