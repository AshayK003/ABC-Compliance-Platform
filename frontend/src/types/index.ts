export interface Centre {
  id: string;
  name: string;
  code: string;
  district: string;
  state: string;
  capacity: number;
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  complianceScore?: number;
  surgeriesThisMonth?: number;
}

export interface Staff {
  id: string;
  centre_id: string;
  name: string;
  role: 'vet' | 'surgeon' | 'admin';
  phone: string;
  password_hash: string;
  active: boolean;
}

export interface Dog {
  id: string;
  centre_id: string;
  tag_id: string;
  sex: 'male' | 'female';
  age_estimate?: number;
  weight?: number;
  status: string;
}

export interface Surgery {
  id: string;
  dog_id: string;
  centre_id: string;
  staff_id: string;
  surgery_type: string;
  weight?: number;
  complications?: string;
  timestamp: string;
  synced_at?: string;
  audit_hash?: string;
}

export interface Inspection {
  id: string;
  centre_id: string;
  inspector_id: string;
  scheduled_at?: string;
  conducted_at?: string;
  status: 'scheduled' | 'completed' | 'overdue';
  findings?: string;
  signoff_hash?: string;
}

export interface Grant {
  id: string;
  awbi_ref: string;
  amount: number;
  purpose: string;
  financial_year: string;
  status: string;
}

export interface Allocation {
  id: string;
  grant_id: string;
  centre_id: string;
  amount: number;
  allocated_at: string;
}

export interface Expense {
  id: string;
  allocation_id: string;
  surgery_id?: string;
  category: string;
  amount: number;
  bill_ref?: string;
  expense_at: string;
}

export interface Complaint {
  id: string;
  centre_id: string;
  citizen_phone: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  sla_deadline?: string;
  resolution?: string;
  created_at: string;
}

export interface SyncQueueItem {
  id: string;
  entity_type: string;
  entity_id: string;
  operation: 'create' | 'update' | 'delete';
  payload: Record<string, unknown>;
  idempotency_key: string;
  status: 'pending' | 'synced' | 'failed';
  retry_count: number;
  created_at: string;
  synced_at?: string;
  error?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  role: string;
}

export interface LoginResponse extends AuthResponse {}

export interface RegisterResponse {
  id: string;
  name: string;
  role: string;
  access_token: string;
}

export interface TokenPayload {
  user_id: string;
  role: string;
  name?: string;
  phone?: string;
  centre_id?: string;
}

export interface User {
  user_id: string;
  name: string;
  role: string;
  centre_id?: string;
  phone?: string;
}