export interface CentreSummary {
  id: string;
  name: string;
  code: string;
  district: string;
  state: string;
  capacity: number;
  status: 'active' | 'inactive' | 'suspended';
  complianceScore: number;
  surgeriesThisMonth: number;
  created_at: string;
}

export interface AlertItem {
  centre: string;
  district: string;
  issue: string;
  status: 'Critical' | 'Warning' | 'Resolved';
}

export interface InspectionRecord {
  id: string;
  centreName: string;
  centreCode: string;
  scheduledAt: string;
  status: 'Scheduled' | 'Completed' | 'Overdue';
  inspectorName: string;
  priority?: 'High' | 'Normal';
  type: string;
}

export interface SurgeryRecord {
  id: string;
  date: string;
  centreName: string;
  centreCode: string;
  animalId: string;
  procedureType: string;
  outcome: 'Recovered' | 'In Observation' | 'Complication';
}

export interface SurgerySummary {
  total: number;
  preOp: number;
  postOp: number;
  complications: number;
}

export interface FundDisbursement {
  date: string;
  centre: string;
  amount: number;
  purpose: string;
  status: 'Approved' | 'Processing' | 'Flagged';
}

export interface ExpenseRecord {
  date: string;
  allocation: string;
  category: string;
  amount: number;
  billRef: string;
  status: 'Paid' | 'Pending';
}

export interface ReportTemplate {
  id: string;
  name: string;
  code: string;
  icon: string;
  color: string;
}

// Shared mock data - single source of truth
export const MOCK_CENTRES: CentreSummary[] = [
  { id: '1', name: 'Metro North ABC Hub', code: 'MNAH-001', district: 'North District', state: 'State', capacity: 450, status: 'active', complianceScore: 92, surgeriesThisMonth: 245, created_at: '2024-01-15T10:00:00Z' },
  { id: '2', name: 'Southside Animal Welfare', code: 'SAW-002', district: 'South District', state: 'State', capacity: 200, status: 'active', complianceScore: 78, surgeriesThisMonth: 180, created_at: '2024-02-20T10:00:00Z' },
  { id: '3', name: 'East Valley ABC Clinic', code: 'EVAC-003', district: 'East District', state: 'State', capacity: 150, status: 'inactive', complianceScore: 45, surgeriesThisMonth: 0, created_at: '2024-03-10T10:00:00Z' },
  { id: '4', name: 'West End Veterinary Trust', code: 'WEVT-004', district: 'West District', state: 'State', capacity: 500, status: 'active', complianceScore: 98, surgeriesThisMonth: 320, created_at: '2024-01-05T10:00:00Z' },
];

export const MOCK_CENTRES_EXTENDED: CentreSummary[] = [
  ...MOCK_CENTRES,
  { id: '1042', name: 'Metro North ABC Hub', code: 'MNAH-001', district: 'North District', state: 'State', capacity: 450, status: 'active', complianceScore: 92, surgeriesThisMonth: 245, created_at: '2024-01-15T10:00:00Z' },
  { id: '1045', name: 'Southside Animal Welfare', code: 'SAW-002', district: 'South District', state: 'State', capacity: 200, status: 'active', complianceScore: 78, surgeriesThisMonth: 180, created_at: '2024-02-20T10:00:00Z' },
  { id: '1018', name: 'East Valley ABC Clinic', code: 'EVAC-003', district: 'East District', state: 'State', capacity: 150, status: 'inactive', complianceScore: 45, surgeriesThisMonth: 0, created_at: '2024-03-10T10:00:00Z' },
  { id: '1088', name: 'West End Veterinary Trust', code: 'WEVT-004', district: 'West District', state: 'State', capacity: 500, status: 'active', complianceScore: 98, surgeriesThisMonth: 320, created_at: '2024-01-05T10:00:00Z' },
  { id: '1092', name: 'Central Municipal Pound', code: 'CMP-005', district: 'Central District', state: 'State', capacity: 300, status: 'active', complianceScore: 85, surgeriesThisMonth: 150, created_at: '2024-04-12T10:00:00Z' },
  { id: '1105', name: 'Rural Care Centre', code: 'RCC-006', district: 'Rural District', state: 'State', capacity: 100, status: 'suspended', complianceScore: 30, surgeriesThisMonth: 0, created_at: '2024-05-01T10:00:00Z' },
];

export const MOCK_ALERTS: AlertItem[] = [
  { centre: 'Southside ABC', district: 'District 2', issue: 'Post-op care protocol violation reported.', status: 'Critical' },
  { centre: 'East Valley Shelter', district: 'District 5', issue: 'Delayed monthly surgery reporting.', status: 'Warning' },
  { centre: 'Central Gov ABC', district: 'District 1', issue: 'Minor infrastructure gap identified during inspection.', status: 'Resolved' },
];

export const MOCK_UPCOMING_INSPECTIONS: Array<{ centreName: string; scheduledAt: string; status: 'Scheduled' | 'Completed' | 'Overdue' }> = [
  { centreName: 'Apex Care Centre', scheduledAt: '2023-10-24', status: 'Scheduled' },
  { centreName: 'Metro Paws ABC', scheduledAt: '2023-10-22', status: 'Completed' },
  { centreName: 'City Ward 4 Clinic', scheduledAt: '2023-10-15', status: 'Overdue' },
  { centreName: 'North District Hub', scheduledAt: '2023-11-02', status: 'Scheduled' },
];

export const MOCK_INSPECTIONS: InspectionRecord[] = [
  { id: 'INS-2948', centreName: 'City Municipal Dog Pound', centreCode: 'CMDP-01', scheduledAt: '2024-10-24T09:00:00', status: 'Scheduled', inspectorName: 'Inspector Dan', priority: 'High', type: 'Routine + Surgery Audit' },
  { id: 'INS-2949', centreName: 'Green Valley Animal Shelter', centreCode: 'GVAS-02', scheduledAt: '2024-10-24T14:30:00', status: 'Scheduled', inspectorName: 'Inspector Dan', priority: 'Normal', type: 'Follow-up on violations' },
  { id: 'INS-2950', centreName: 'Westside ABC Centre', centreCode: 'WABC-03', scheduledAt: '2024-10-25T10:00:00', status: 'Scheduled', inspectorName: 'Inspector Dan', priority: 'Normal', type: 'Initial registration' },
  { id: 'INS-2947', centreName: 'North District Hub', centreCode: 'NDH-04', scheduledAt: '2024-10-23T09:00:00', status: 'Completed', inspectorName: 'Inspector Dan', priority: 'Normal', type: 'Routine' },
  { id: 'INS-2946', centreName: 'East Valley Shelter', centreCode: 'EVS-05', scheduledAt: '2024-10-22T11:00:00', status: 'Overdue', inspectorName: 'Inspector Dan', priority: 'High', type: 'Follow-up' },
];

export const MOCK_SURGERY_SUMMARY: SurgerySummary = {
  total: 1248,
  preOp: 342,
  postOp: 856,
  complications: 50,
};

export const MOCK_SURGERIES: SurgeryRecord[] = [
  { id: '1', date: '2023-10-24 14:30', centreName: 'Central Vet Hub', centreCode: 'CVH-01', animalId: 'DOG-8842-A', procedureType: 'Orthopedic - Fracture Repair', outcome: 'Recovered' },
  { id: '2', date: '2023-10-24 15:15', centreName: 'Northside Clinic', centreCode: 'NSC-04', animalId: 'CAT-1193-B', procedureType: 'Soft Tissue - Exploratory', outcome: 'In Observation' },
  { id: '3', date: '2023-10-24 16:00', centreName: 'East End Surgery', centreCode: 'EES-02', animalId: 'DOG-9921-C', procedureType: 'Cardiothoracic', outcome: 'Complication' },
  { id: '4', date: '2023-10-24 16:45', centreName: 'Central Vet Hub', centreCode: 'CVH-01', animalId: 'CAT-4432-A', procedureType: 'Dental Extraction', outcome: 'Recovered' },
  { id: '5', date: '2023-10-24 10:30', centreName: 'West End Surgery', centreCode: 'WES-03', animalId: 'DOG-7721-B', procedureType: 'Ophthalmic - Cataract', outcome: 'Recovered' },
  { id: '6', date: '2023-10-23 14:00', centreName: 'Northside Clinic', centreCode: 'NSC-04', animalId: 'CAT-3382-C', procedureType: 'Neurological - Spinal', outcome: 'In Observation' },
];

export const MOCK_FUND_DISBURSEMENTS: FundDisbursement[] = [
  { date: '2023-10-24', centre: 'North Regional Hub', amount: 12500000, purpose: 'Infrastructure Upgrade', status: 'Approved' },
  { date: '2023-10-22', centre: 'Eastern Tech Park', amount: 8250000, purpose: 'Operational Costs Q4', status: 'Processing' },
  { date: '2023-10-18', centre: 'South District Hq', amount: 4100000, purpose: 'Training & Compliance', status: 'Approved' },
  { date: '2023-10-15', centre: 'Central Data Center', amount: 22000000, purpose: 'Server Procurement', status: 'Flagged' },
  { date: '2023-10-10', centre: 'West Operations Facility', amount: 5750000, purpose: 'Facility Maintenance', status: 'Approved' },
];

export const MOCK_EXPENSES: ExpenseRecord[] = [
  { date: '2023-10-24', allocation: 'A1', category: 'medicine', amount: 2500000, billRef: 'BILL-001', status: 'Paid' },
  { date: '2023-10-22', allocation: 'A1', category: 'equipment', amount: 15000000, billRef: 'BILL-002', status: 'Pending' },
  { date: '2023-10-18', allocation: 'A2', category: 'infrastructure', amount: 8000000, billRef: 'BILL-003', status: 'Paid' },
];

export const MOCK_REPORT_TEMPLATES: ReportTemplate[] = [
  { id: 'TMPL-001', name: 'Monthly Compliance', code: 'TMPL-001', icon: 'summarize', color: 'primary' },
  { id: 'TMPL-042', name: 'Surgery Trends', code: 'TMPL-042', icon: 'trending_up', color: 'secondary' },
  { id: 'TMPL-108', name: 'Inspection Summary', code: 'TMPL-108', icon: 'plagiarism', color: 'tertiary' },
  { id: 'TMPL-205', name: 'Financial Audit', code: 'TMPL-205', icon: 'account_balance', color: 'error' },
];

// Date constants
export const MOCK_DATES = {
  DASHBOARD_INSPECTION_DATE_1: '2023-10-24',
  DASHBOARD_INSPECTION_DATE_2: '2023-10-22',
  DASHBOARD_INSPECTION_DATE_3: '2023-10-15',
  DASHBOARD_INSPECTION_DATE_4: '2023-11-02',
  FUND_DATE_1: '2023-10-24',
  FUND_DATE_2: '2023-10-22',
  FUND_DATE_3: '2023-10-18',
  FUND_DATE_4: '2023-10-15',
  FUND_DATE_5: '2023-10-10',
  INSPECTION_DATE_1: '2024-10-24T09:00:00',
  INSPECTION_DATE_2: '2024-10-24T14:30:00',
  INSPECTION_DATE_3: '2024-10-25T10:00:00',
  INSPECTION_DATE_4: '2024-10-23T09:00:00',
  INSPECTION_DATE_5: '2024-10-22T11:00:00',
  SURGERY_DATE_1: '2023-10-24 14:30',
  SURGERY_DATE_2: '2023-10-24 15:15',
  SURGERY_DATE_3: '2023-10-24 16:00',
  SURGERY_DATE_4: '2023-10-24 16:45',
  SURGERY_DATE_5: '2023-10-24 10:30',
  SURGERY_DATE_6: '2023-10-23 14:00',
} as const;