import type { Dog, Surgery } from '../../types';
import { authenticatedFetch as request } from './client';

export const surgeriesApi = {
  getSurgeries: (params?: { centre_id?: string; dog_id?: string; from_date?: string; to_date?: string; limit?: number; offset?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<Surgery[]>(`/surgeries${query}`);
  },
  getSurgery: (id: string) => request<Surgery>(`/surgeries/${id}`),
  createSurgery: (data: { dog_id: string; centre_id: string; staff_id: string; surgery_type: string; weight?: number; complications?: string; timestamp?: string }) =>
    request<Surgery>('/surgeries', { method: 'POST', body: JSON.stringify(data) }),
  getDogs: (params?: { centre_id?: string }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<Dog[]>(`/dogs${query}`);
  },
};