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
};
