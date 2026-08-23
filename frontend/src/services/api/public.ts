import type { Complaint, SyncQueueItem } from '../../types';
import { authenticatedFetch as request } from './client';

interface HeatmapState {
  state: string;
  centres: number;
  inspections: number;
  compliance_rate: number;
  risk: 'critical' | 'moderate' | 'compliant';
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

  // Heatmap + real per-centre compliance scores
  getHeatmap: () => request<HeatmapState[]>('/public/heatmap'),
  getComplianceScores: () => request<Array<{
    centre_id: string;
    compliance_score: number;
    completed_inspections: number;
    total_inspections: number;
  }>>('/public/compliance-scores'),

  // Committee governance (Committee Portal)
  getCommitteeDecisions: (limit = 10) =>
    request<Array<{
      id: string;
      resolution_id: string;
      subject: string;
      status: string;
      decided_at: string | null;
      tally: { yes: number; no: number; abstain: number };
    }>>(`/committee/decisions?limit=${limit}`),
  getCommitteeMeetings: (limit = 5) =>
    request<Array<{
      id: string;
      title: string;
      scheduled_at: string;
      location: string | null;
      meeting_type: string;
      status: string;
    }>>(`/committee/meetings?limit=${limit}`),
  getCommitteeDocuments: (limit = 8) =>
    request<Array<{
      id: string;
      title: string;
      file_type: string;
      file_size: number;
      uploaded_at: string;
    }>>(`/committee/documents?limit=${limit}`),
  getCommitteeMembers: () =>
    request<Array<{
      id: string;
      name: string;
      phone: string;
      role: string;
      joined_at: string;
    }>>('/committee/members'),
};