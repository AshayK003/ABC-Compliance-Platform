import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Surgeries } from '../pages/Surgeries';

// Mock the api module
vi.mock('../services/api', () => ({
  api: {
    getSurgeries: vi.fn(),
    getCentres: vi.fn(),
    createSurgery: vi.fn(),
  },
}));

import { api } from '../services/api';

const mockedApi = vi.mocked(api);

const centresPaginated = {
  data: [
    { id: 'c1', name: 'Centre One', code: 'C1' },
    { id: 'c2', name: 'Centre Two', code: 'C2' },
  ],
  total: 2,
  page: 1,
  pageSize: 50,
};

const centresArray = [
  { id: 'c1', name: 'Centre One', code: 'C1' },
];

const surgeries = [
  {
    id: 's1',
    dog_id: 'd1',
    centre_id: 'c1',
    surgery_type: 'spay',
    timestamp: '2026-08-01T10:00:00',
    complications: null,
  },
  {
    id: 's2',
    dog_id: 'd2',
    centre_id: 'c2',
    surgery_type: 'neuter',
    timestamp: '2026-08-02T10:00:00',
    complications: 'bleeding',
  },
];

describe('Surgeries data loading', () => {
  it('maps paginated centre response and shows records', async () => {
    mockedApi.getSurgeries.mockResolvedValue(surgeries as never);
    mockedApi.getCentres.mockResolvedValue(centresPaginated as never);

    render(<Surgeries />);

    await waitFor(() => {
      expect(screen.getByText(/centre one/i)).toBeTruthy();
    });
    // Both surgeries present
    expect(screen.getByText(/centre two/i)).toBeTruthy();
  });

  it('handles bare-array centre response without throwing', async () => {
    mockedApi.getSurgeries.mockResolvedValue(surgeries as never);
    mockedApi.getCentres.mockResolvedValue(centresArray as never);

    render(<Surgeries />);

    await waitFor(() => {
      expect(screen.getByText(/centre one/i)).toBeTruthy();
    });
  });

  it('shows empty state when no surgeries exist', async () => {
    mockedApi.getSurgeries.mockResolvedValue([] as never);
    mockedApi.getCentres.mockResolvedValue(centresPaginated as never);

    render(<Surgeries />);

    await waitFor(() => {
      expect(screen.getByText(/no surgeries recorded/i)).toBeTruthy();
    });
  });
});
