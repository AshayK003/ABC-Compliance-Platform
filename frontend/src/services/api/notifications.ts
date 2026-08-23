import type { Notification } from '../../types';
import { authenticatedFetch as request } from './client';

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