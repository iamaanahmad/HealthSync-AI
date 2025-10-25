/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('../../lib/auth');

jest.mock('../../hooks/use-toast', () => ({
  useToast: jest.fn(),
}));

import { useRouter } from 'next/navigation';
import { LoginForm } from '../../components/auth/login-form';
import { AuthService } from '../../lib/auth';
import { useToast } from '../../hooks/use-toast';

const mockPush = jest.fn();
const mockToast = jest.fn();

const mockAuthService = AuthService as jest.Mocked<typeof AuthService>;

describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    (useToast as jest.Mock).mockReturnValue({ toast: mockToast });
  });

  it('should render login form with all fields', () => {
    render(<LoginForm />);

    expect(screen.getByText('Patient Login')).toBeInTheDocument();
    expect(screen.getByLabelText('Patient ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
  });

  it('should display demo credentials', () => {
    render(<LoginForm />);

    expect(screen.getByText('Demo Credentials:')).toBeInTheDocument();
    expect(screen.getByText('Patient ID: P001, Password: password123')).toBeInTheDocument();
    expect(screen.getByText('Patient ID: P002, Password: password456')).toBeInTheDocument();
  });

  it('should handle successful login', async () => {
    const user = userEvent.setup();
    const mockSession = {
      patientId: 'P001',
      isAuthenticated: true,
      profile: { firstName: 'John', lastName: 'Doe' },
      sessionToken: 'mock-token',
      expiresAt: new Date(),
    };

    mockAuthService.login.mockResolvedValue({
      success: true,
      session: mockSession,
    });

    render(<LoginForm />);

    await user.type(screen.getByLabelText('Patient ID'), 'P001');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(mockAuthService.login).toHaveBeenCalledWith({
        patientId: 'P001',
        password: 'password123',
      });
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Login Successful',
      description: 'Welcome back, John!',
    });

    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('should handle login failure', async () => {
    const user = userEvent.setup();

    mockAuthService.login.mockResolvedValue({
      success: false,
      error: 'Invalid patient ID or password',
    });

    render(<LoginForm />);

    await user.type(screen.getByLabelText('Patient ID'), 'INVALID');
    await user.type(screen.getByLabelText('Password'), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid patient ID or password')).toBeInTheDocument();
    });

    expect(mockToast).not.toHaveBeenCalled();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('should show loading state during login', async () => {
    const user = userEvent.setup();

    mockAuthService.login.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    render(<LoginForm />);

    await user.type(screen.getByLabelText('Patient ID'), 'P001');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(screen.getByText('Signing in...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
  });

  it('should call onSuccess callback when provided', async () => {
    const user = userEvent.setup();
    const onSuccess = jest.fn();

    mockAuthService.login.mockResolvedValue({
      success: true,
      session: { profile: { firstName: 'John' } },
    });

    render(<LoginForm onSuccess={onSuccess} />);

    await user.type(screen.getByLabelText('Patient ID'), 'P001');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });

    expect(mockPush).not.toHaveBeenCalled();
  });

  it('should handle network errors gracefully', async () => {
    const user = userEvent.setup();

    mockAuthService.login.mockRejectedValue(new Error('Network error'));

    render(<LoginForm />);

    await user.type(screen.getByLabelText('Patient ID'), 'P001');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(screen.getByText('An unexpected error occurred. Please try again.')).toBeInTheDocument();
    });
  });
});