import type { ReportTemplate, ReportGenerateRequest, ReportPreviewResponse } from '../../types';
import { authenticatedFetch as request } from './client';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';

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

/** Trigger a browser download of a blob, deriving the filename from Content-Disposition. */
function download(response: Response, fallbackName: string): Promise<void> {
  return response.blob().then((blob) => {
    const cd = response.headers.get('content-disposition') ?? '';
    const match = /filename="?([^";]+)"?/.exec(cd);
    const filename = match ? match[1] : fallbackName;
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  });
}

/** POST the report params and download the resulting PDF/Excel file.
 * Auth via the httpOnly access-token cookie (credentials: 'include'). */
async function exportFile(
  suffix: 'pdf' | 'excel',
  data: ReportGenerateRequest,
): Promise<void> {
  const response = await fetch(`${API_BASE}/reports/export/${suffix}`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Export failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  await download(
    response,
    `${data.template_id.toLowerCase().replace(/-/g, '_')}.${suffix === 'pdf' ? 'pdf' : 'xlsx'}`,
  );
}

/** File exports — themed PDF (pdf-studio) and styled Excel (openpyxl). */
export const reportsExport = {
  exportPdf: (data: ReportGenerateRequest) => exportFile('pdf', data),
  exportExcel: (data: ReportGenerateRequest) => exportFile('excel', data),
};
