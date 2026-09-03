import { describe, it, expect } from 'vitest';
import { normalizeCentresResponse } from './centres';
import type { Centre } from '../../types';

const centre = (id: string): Centre => ({
  id,
  name: `Centre ${id}`,
  code: id.toUpperCase(),
  district: 'Lucknow',
  state: 'Uttar Pradesh',
  capacity: 10,
  status: 'active',
  created_at: '2026-01-01T00:00:00',
});

describe('normalizeCentresResponse', () => {
  it('passes a bare array through (legacy shape)', () => {
    expect(normalizeCentresResponse([centre('a')])).toHaveLength(1);
  });

  it('unwraps the paginated envelope (backend shape)', () => {
    const envelope = { data: [centre('a'), centre('b')], total: 2, page: 1, pageSize: 50 };
    const list = normalizeCentresResponse(envelope);
    expect(list).toHaveLength(2);
    expect(list[0].id).toBe('a');
  });

  it('returns [] for null, undefined, or malformed payloads', () => {
    expect(normalizeCentresResponse(null)).toEqual([]);
    expect(normalizeCentresResponse(undefined)).toEqual([]);
    expect(normalizeCentresResponse({})).toEqual([]);
    expect(normalizeCentresResponse({ data: null })).toEqual([]);
  });
});
