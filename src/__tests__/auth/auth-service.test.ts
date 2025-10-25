/**
 * @jest-environment jsdom
 */

import { AuthService, PatientLoginSchema } from '@/lib/auth';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      const credentials = {
        patientId: 'P001',
        password: 'password123',
      };

      const result = await AuthService.login(credentials);

      expect(result.success).toBe(true);
      expect(result.session).toBeDefined();
      expect(result.session?.patientId).toBe('P001');
      expect(result.session?.profile?.firstName).toBe('John');
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'healthsync_patient_session',
        expect.any(String)
      );
    });

    it('should fail login with invalid patient ID', async () => {
      const credentials = {
        patientId: 'INVALID',
        password: 'password123',
      };

      const result = await AuthService.login(credentials);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid patient ID or password');
      expect(result.session).toBeUndefined();
    });

    it('should fail login with invalid password', async () => {
      const credentials = {
        patientId: 'P001',
        password: 'wrongpassword',
      };

      const result = await AuthService.login(credentials);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid patient ID or password');
      expect(result.session).toBeUndefined();
    });

    it('should validate credentials with schema', () => {
      const validCredentials = {
        patientId: 'P001',
        password: 'password123',
      };

      const invalidCredentials = {
        patientId: '',
        password: '123',
      };

      expect(() => PatientLoginSchema.parse(validCredentials)).not.toThrow();
      expect(() => PatientLoginSchema.parse(invalidCredentials)).toThrow();
    });
  });

  describe('logout', () => {
    it('should remove session from localStorage', () => {
      AuthService.logout();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith(
        'healthsync_patient_session'
      );
    });
  });

  describe('getCurrentSession', () => {
    it('should return null when no session exists', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const session = AuthService.getCurrentSession();

      expect(session).toBeNull();
    });

    it('should return session when valid session exists', () => {
      const mockSession = {
        patientId: 'P001',
        isAuthenticated: true,
        profile: {
          patientId: 'P001',
          firstName: 'John',
          lastName: 'Doe',
          dateOfBirth: '1985-06-15',
          email: 'john.doe@email.com',
        },
        sessionToken: 'mock-token',
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockSession));

      const session = AuthService.getCurrentSession();

      expect(session).toBeDefined();
      expect(session?.patientId).toBe('P001');
      expect(session?.isAuthenticated).toBe(true);
    });

    it('should return null and logout when session is expired', () => {
      const expiredSession = {
        patientId: 'P001',
        isAuthenticated: true,
        profile: null,
        sessionToken: 'mock-token',
        expiresAt: new Date(Date.now() - 1000).toISOString(), // Expired
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(expiredSession));

      const session = AuthService.getCurrentSession();

      expect(session).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(
        'healthsync_patient_session'
      );
    });

    it('should return null when session data is corrupted', () => {
      localStorageMock.getItem.mockReturnValue('invalid-json');

      const session = AuthService.getCurrentSession();

      expect(session).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when valid session exists', () => {
      const mockSession = {
        patientId: 'P001',
        isAuthenticated: true,
        profile: null,
        sessionToken: 'mock-token',
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockSession));

      expect(AuthService.isAuthenticated()).toBe(true);
    });

    it('should return false when no session exists', () => {
      localStorageMock.getItem.mockReturnValue(null);

      expect(AuthService.isAuthenticated()).toBe(false);
    });

    it('should return false when session is expired', () => {
      const expiredSession = {
        patientId: 'P001',
        isAuthenticated: true,
        profile: null,
        sessionToken: 'mock-token',
        expiresAt: new Date(Date.now() - 1000).toISOString(),
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(expiredSession));

      expect(AuthService.isAuthenticated()).toBe(false);
    });
  });
});