export * from './auth';
export * from './centres';
export * from './surgeries';
export * from './inspections';
export * from './funds';
export * from './public';

// Re-export types
export type { Centre, Dog, Surgery, Inspection, Grant, Allocation, Expense, Complaint, SyncQueueItem, User, LoginResponse, RegisterResponse, TokenPayload, AuthResponse } from '../../types';

// Legacy setAuthToken - delegates to each module
import { setAuthToken as setAuthTokenAuth } from './auth';
import { setAuthToken as setAuthTokenCentres } from './centres';
import { setAuthToken as setAuthTokenSurgeries } from './surgeries';
import { setAuthToken as setAuthTokenInspections } from './inspections';
import { setAuthToken as setAuthTokenFunds } from './funds';
import { setAuthToken as setAuthTokenPublic } from './public';

export function setAuthToken(token: string | null | undefined) {
  setAuthTokenAuth(token);
  setAuthTokenCentres(token);
  setAuthTokenSurgeries(token);
  setAuthTokenInspections(token);
  setAuthTokenFunds(token);
  setAuthTokenPublic(token);
}

// Legacy api object for backward compatibility during migration
import { authApi } from './auth';
import { centresApi } from './centres';
import { surgeriesApi } from './surgeries';
import { inspectionsApi } from './inspections';
import { fundsApi } from './funds';
import { publicApi } from './public';

export const api = {
  // Auth
  login: authApi.login,
  register: authApi.register,
  getMe: authApi.getMe,
  refresh: authApi.refresh,
  logout: authApi.logout,
  deleteAccount: authApi.deleteAccount,
  // Centres
  getCentres: centresApi.getCentres,
  getCentre: centresApi.getCentre,
  createCentre: centresApi.createCentre,
  // Dogs (placeholder - not split yet)
  getDogs: () => Promise.resolve([]),
  getDog: () => Promise.resolve(null),
  createDog: () => Promise.resolve(null),
  // Surgeries
  getSurgeries: surgeriesApi.getSurgeries,
  getSurgery: surgeriesApi.getSurgery,
  createSurgery: surgeriesApi.createSurgery,
  // Inspections
  getInspections: inspectionsApi.getInspections,
  getInspection: inspectionsApi.getInspection,
  createInspection: inspectionsApi.createInspection,
  // Grants
  getGrants: fundsApi.getGrants,
  getGrant: fundsApi.getGrant,
  createGrant: fundsApi.createGrant,
  // Allocations
  getAllocations: fundsApi.getAllocations,
  createAllocation: fundsApi.createAllocation,
  // Expenses
  getExpenses: fundsApi.getExpenses,
  createExpense: fundsApi.createExpense,
  // Complaints
  getComplaints: publicApi.getComplaints,
  createComplaint: publicApi.createComplaint,
  updateComplaint: publicApi.updateComplaint,
  // Sync Queue
  enqueueSync: publicApi.enqueueSync,
  getPendingSync: publicApi.getPendingSync,
  markSynced: publicApi.markSynced,
  markFailed: publicApi.markFailed,
  retryFailed: publicApi.retryFailed,
  getSyncStatus: publicApi.getSyncStatus,
};