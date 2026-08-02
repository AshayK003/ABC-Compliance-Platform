import type { Grant, Allocation, Expense } from '../../types';

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

export const fundsApi = {
  // Grants
  getGrants: (params?: { limit?: number; offset?: number }) => {
    const search = new URLSearchParams();
    if (params?.limit) search.set('limit', String(params.limit));
    if (params?.offset) search.set('offset', String(params.offset));
    const query = search.toString() ? `?${search}` : '';
    return request<Grant[]>(`/grants${query}`);
  },
  getGrant: (id: string) => request<Grant>(`/grants/${id}`),
  createGrant: (data: { awbi_ref: string; amount: number; purpose: string; financial_year: string; status?: string }) =>
    request<Grant>('/grants', { method: 'POST', body: JSON.stringify(data) }),

  // Allocations
  getAllocations: (params?: { grant_id?: string; centre_id?: string; limit?: number; offset?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<Allocation[]>(`/allocations${query}`);
  },
  getAllocation: (id: string) => request<Allocation>(`/allocations/${id}`),
  createAllocation: (data: { grant_id: string; centre_id: string; amount: number }) =>
    request<Allocation>('/allocations', { method: 'POST', body: JSON.stringify(data) }),

  // Expenses
  getExpenses: (params?: { allocation_id?: string; limit?: number; offset?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<Expense[]>(`/expenses${query}`);
  },
  getExpense: (id: string) => request<Expense>(`/expenses/${id}`),
  createExpense: (data: { allocation_id: string; surgery_id?: string; category: string; amount: number; bill_ref?: string; expense_at?: string }) =>
    request<Expense>('/expenses', { method: 'POST', body: JSON.stringify(data) }),
};