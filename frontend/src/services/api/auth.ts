import type { User, LoginResponse, RegisterResponse } from '../../types';
import { authenticatedFetch, setAuthToken } from './client';

export { setAuthToken };

export const authApi = {
  login: (phone: string, password: string) =>
    authenticatedFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
    }),

  register: (data: { name: string; phone: string; password: string; centre_id?: string }) =>
    authenticatedFetch<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMe: () => authenticatedFetch<User>('/auth/me'),
  refresh: () => authenticatedFetch<LoginResponse>('/auth/refresh', { method: 'POST' }),
  logout: () => authenticatedFetch<{ message: string }>('/auth/logout', { method: 'POST' }),
  deleteAccount: () => authenticatedFetch<{ message: string }>('/auth/me', { method: 'DELETE' }),

  // Admin user management (approval of pending registrations, role/centre changes)
  listStaff: (params?: { active?: boolean; centre_id?: string }) => {
    const qs = new URLSearchParams();
    if (params?.active !== undefined) qs.set('active', String(params.active));
    if (params?.centre_id) qs.set('centre_id', params.centre_id);
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return authenticatedFetch<User[]>(`/auth/staff${suffix}`);
  },
  listPendingStaff: () => authenticatedFetch<User[]>('/auth/staff/pending'),
  updateStaff: (staffId: string, data: { active?: boolean; role?: string; centre_id?: string }) =>
    authenticatedFetch<User>(`/auth/staff/${staffId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};
