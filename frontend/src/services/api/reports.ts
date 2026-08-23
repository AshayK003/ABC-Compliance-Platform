import type { ReportTemplate, ReportGenerateRequest, ReportPreviewResponse } from '../../types';
import { authenticatedFetch as request } from './client';

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