import type { Notification } from '../../types';

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

export const notificationsApi = {
  getNotifications: (params?: { user_id?: string; read?: boolean; limit?: number; offset?: number }) => {
    const search = new URLSearchParams();
    if (params?.user_id) search.set('user_id', params.user_id);
    if (params?.read !== undefined) search.set('read', String(params.read));
    if (params?.limit) search.set('limit', String(params.limit));
    if (params?.offset) search.set('offset', String(params.offset));
    const query = search.toString() ? `?${search}` : '';
    return request<Notification[]>(`/notifications${query}`);
  },

  getNotification: (id: string) => request<Notification>(`/notifications/${id}`),

  createNotification: (data: { user_id: string; title: string; message: string; type?: string; read?: boolean }) =>
    request<Notification>('/notifications', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateNotification: (id: string, data: { read?: boolean; title?: string; message?: string; type?: string }) =>
    request<Notification>(`/notifications/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  markAllRead: (user_id?: string) =>
    request<{ updated: number }>('/notifications/mark-all-read', {
      method: 'POST',
      body: JSON.stringify({ user_id }),
    }),

  getUnreadCount: (user_id?: string) =>
    request<{ count: number }>(`/notifications/unread-count${user_id ? `?user_id=${user_id}` : ''}`),
};