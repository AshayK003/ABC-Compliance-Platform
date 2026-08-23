import type { Inspection } from '../../types';
import { authenticatedFetch as request } from './client';

export const inspectionsApi = {
  getInspections: (params?: { centre_id?: string; status?: string; limit?: number; offset?: number }) => {
    const search = new URLSearchParams(params as Record<string, string>);
    const query = search.toString() ? `?${search}` : '';
    return request<Inspection[]>(`/inspections${query}`);
  },
  getInspection: (id: string) => request<Inspection>(`/inspections/${id}`),
  createInspection: (data: { centre_id: string; inspector_id: string; scheduled_at?: string; status?: string }) =>
    request<Inspection>('/inspections', { method: 'POST', body: JSON.stringify(data) }),
};