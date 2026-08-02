import type { ReportTemplate, ReportGenerateRequest, ReportPreviewResponse } from '../../types';

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

export const reportsApi = {
  // Report Templates
  getTemplates: () => request<ReportTemplate[]>('/reports/templates'),
  getTemplate: (id: string) => request<ReportTemplate>(`/reports/templates/${id}`),

  // Report Generation
  generateReport: (data: ReportGenerateRequest) =>
    request<ReportPreviewResponse>('/reports/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Chart Data
  getYoyAdherence: () => request<{
    quarters: string[];
    current_year: Record<string, number>;
    previous_year: Record<string, number>;
  }>('/reports/charts/yoy-adherence'),

  getMonthlyDisbursements: () => request<{
    months: string[];
    amounts: number[];
  }>('/reports/charts/monthly-disbursements'),

  getExpenseCategories: () => request<{
    categories: Array<{
      category: string;
      amount: number;
      percentage: number;
    }>;
  }>('/reports/charts/expense-categories'),

  getMonthlySurgeries: () => request<{
    months: string[];
    counts: number[];
  }>('/reports/charts/monthly-surgeries'),
};