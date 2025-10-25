/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock dependencies
jest.mock('../../lib/auth');

import { ProfileCard } from '../../components/patient/profile-card';
import { AuthService } from '../../lib/auth';

const mockProfile = {
  patientId: 'P001',
  firstName: 'John',
  lastName: 'Doe',
  dateOfBirth: '1985-06-15',
  email: 'john.doe@email.com',
  phone: '+1-555-0123',
  emergencyContact: {
    name: 'Jane Doe',
    phone: '+1-555-0124',
    relationship: 'Spouse',
  },
};

const mockSession = {
  patientId: 'P001',
  isAuthenticated: true,
  profile: mockProfile,
  sessionToken: 'mock-session-token-12345',
  expiresAt: new Date('2024-12-31T23:59:59Z'),
};

const mockAuthService = AuthService as jest.Mocked<typeof AuthService>;

describe('ProfileCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render profile information when session exists', () => {
    mockAuthService.getCurrentSession.mockReturnValue(mockSession);

    render(<ProfileCard />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('ID: P001')).toBeInTheDocument();
    expect(screen.getByText('Verified Patient')).toBeInTheDocument();
    expect(screen.getByText('john.doe@email.com')).toBeInTheDocument();
    expect(screen.getByText('+1-555-0123')).toBeInTheDocument();
  });

  it('should display formatted date of birth and age', () => {
    mockAuthService.getCurrentSession.mockReturnValue(mockSession);

    render(<ProfileCard />);

    expect(screen.getByText('June 15, 1985')).toBeInTheDocument();
    // Age calculation may vary based on current date, so we check for pattern
    expect(screen.getByText(/\(\d+ years old\)/)).toBeInTheDocument();
  });

  it('should display emergency contact information', () => {
    mockAuthService.getCurrentSession.mockReturnValue(mockSession);

    render(<ProfileCard />);

    expect(screen.getByText('Emergency Contact')).toBeInTheDocument();
    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(screen.getByText('Spouse')).toBeInTheDocument();
    expect(screen.getByText('+1-555-0124')).toBeInTheDocument();
  });

  it('should display session information', () => {
    mockAuthService.getCurrentSession.mockReturnValue(mockSession);

    render(<ProfileCard />);

    expect(screen.getByText('Session Information')).toBeInTheDocument();
    expect(screen.getByText('mock-session-token...')).toBeInTheDocument();
    expect(screen.getByText(/December 31, 2024/)).toBeInTheDocument();
  });

  it('should display user initials in avatar', () => {
    mockAuthService.getCurrentSession.mockReturnValue(mockSession);

    render(<ProfileCard />);

    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('should render edit button when onEdit prop is provided', () => {
    const onEdit = jest.fn();
    mockAuthService.getCurrentSession.mockReturnValue(mockSession);

    render(<ProfileCard onEdit={onEdit} />);

    const editButton = screen.getByRole('button', { name: /edit profile/i });
    expect(editButton).toBeInTheDocument();
  });

  it('should call onEdit when edit button is clicked', async () => {
    const user = userEvent.setup();
    const onEdit = jest.fn();
    mockAuthService.getCurrentSession.mockReturnValue(mockSession);

    render(<ProfileCard onEdit={onEdit} />);

    const editButton = screen.getByRole('button', { name: /edit profile/i });
    await user.click(editButton);

    expect(onEdit).toHaveBeenCalled();
  });

  it('should not render edit button when onEdit prop is not provided', () => {
    mockAuthService.getCurrentSession.mockReturnValue(mockSession);

    render(<ProfileCard />);

    expect(screen.queryByRole('button', { name: /edit profile/i })).not.toBeInTheDocument();
  });

  it('should handle profile without emergency contact', () => {
    const sessionWithoutEmergencyContact = {
      ...mockSession,
      profile: {
        ...mockProfile,
        emergencyContact: undefined,
      },
    };

    mockAuthService.getCurrentSession.mockReturnValue(sessionWithoutEmergencyContact);

    render(<ProfileCard />);

    expect(screen.queryByText('Emergency Contact')).not.toBeInTheDocument();
    expect(screen.queryByText('Jane Doe')).not.toBeInTheDocument();
  });

  it('should handle profile without phone number', () => {
    const sessionWithoutPhone = {
      ...mockSession,
      profile: {
        ...mockProfile,
        phone: undefined,
      },
    };

    mockAuthService.getCurrentSession.mockReturnValue(sessionWithoutPhone);

    render(<ProfileCard />);

    expect(screen.queryByText('+1-555-0123')).not.toBeInTheDocument();
  });

  it('should display fallback message when no profile is available', () => {
    mockAuthService.getCurrentSession.mockReturnValue(null);

    render(<ProfileCard />);

    expect(screen.getByText('Profile information not available')).toBeInTheDocument();
  });

  it('should handle invalid date formats gracefully', () => {
    const sessionWithInvalidDate = {
      ...mockSession,
      profile: {
        ...mockProfile,
        dateOfBirth: 'invalid-date',
      },
    };

    mockAuthService.getCurrentSession.mockReturnValue(sessionWithInvalidDate);

    render(<ProfileCard />);

    expect(screen.getByText('invalid-date')).toBeInTheDocument();
  });
});