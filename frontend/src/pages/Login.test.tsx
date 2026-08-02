import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { vi } from 'vitest';

// Mock the API
vi.mock('../services/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
    deleteAccount: vi.fn(),
  },
  setAuthToken: vi.fn(),
}));

const TestLoginForm = () => {
  const { user, login, loading, isAuthenticated } = useAuth();
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="user">{user ? user.name : 'no-user'}</div>
      <button 
        onClick={() => login({ phone: '9876543210', password: 'password123' })} 
        data-testid="login-btn"
      >
        Login
      </button>
    </div>
  );
};

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TestLoginForm />
        </AuthProvider>
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('loading')).toHaveTextContent('loading');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
  });

  it('shows authenticated user after login', async () => {
    const { authApi } = await import('../services/api/auth');
    vi.mocked(authApi.login).mockResolvedValue({ 
      access_token: 'token123',
      token_type: 'bearer',
      user_id: 'user1',
      role: 'vet'
    });
    vi.mocked(authApi.getMe).mockResolvedValue({
      user_id: 'user1',
      name: 'Dr. Test',
      role: 'vet',
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestLoginForm />
        </AuthProvider>
      </MemoryRouter>
    );

    // Wait for initial load to complete
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    // Click login button
    fireEvent.click(screen.getByTestId('login-btn'));

    // Wait for login to complete
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user')).toHaveTextContent('Dr. Test');
    });
  });
});