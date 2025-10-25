// Authentication and session management for patients
import { z } from 'zod';

// Patient authentication schema
export const PatientLoginSchema = z.object({
  patientId: z.string().min(1, 'Patient ID is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

export const PatientProfileSchema = z.object({
  patientId: z.string(),
  firstName: z.string(),
  lastName: z.string(),
  dateOfBirth: z.string(),
  email: z.string().email(),
  phone: z.string().optional(),
  emergencyContact: z.object({
    name: z.string(),
    phone: z.string(),
    relationship: z.string(),
  }).optional(),
});

export type PatientLogin = z.infer<typeof PatientLoginSchema>;
export type PatientProfile = z.infer<typeof PatientProfileSchema>;

// Session management
export interface PatientSession {
  patientId: string;
  isAuthenticated: boolean;
  profile: PatientProfile | null;
  sessionToken: string;
  expiresAt: Date;
}

// Mock authentication service (in real app, this would connect to backend)
export class AuthService {
  private static readonly SESSION_KEY = 'healthsync_patient_session';
  
  // Mock patient database
  private static mockPatients: Record<string, { password: string; profile: PatientProfile }> = {
    'P001': {
      password: 'password123',
      profile: {
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
      },
    },
    'P002': {
      password: 'password456',
      profile: {
        patientId: 'P002',
        firstName: 'Sarah',
        lastName: 'Johnson',
        dateOfBirth: '1990-03-22',
        email: 'sarah.johnson@email.com',
        phone: '+1-555-0125',
        emergencyContact: {
          name: 'Michael Johnson',
          phone: '+1-555-0126',
          relationship: 'Brother',
        },
      },
    },
  };

  static async login(credentials: PatientLogin): Promise<{ success: boolean; session?: PatientSession; error?: string }> {
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const patient = this.mockPatients[credentials.patientId];
      
      if (!patient || patient.password !== credentials.password) {
        return { success: false, error: 'Invalid patient ID or password' };
      }

      const session: PatientSession = {
        patientId: credentials.patientId,
        isAuthenticated: true,
        profile: patient.profile,
        sessionToken: this.generateSessionToken(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
      };

      // Store session in localStorage (in real app, use secure storage)
      if (typeof window !== 'undefined') {
        localStorage.setItem(this.SESSION_KEY, JSON.stringify(session));
      }

      return { success: true, session };
    } catch (error) {
      return { success: false, error: 'Login failed. Please try again.' };
    }
  }

  static logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.SESSION_KEY);
    }
  }

  static getCurrentSession(): PatientSession | null {
    if (typeof window === 'undefined') return null;
    
    try {
      const sessionData = localStorage.getItem(this.SESSION_KEY);
      if (!sessionData) return null;

      const session: PatientSession = JSON.parse(sessionData);
      
      // Check if session is expired
      if (new Date() > new Date(session.expiresAt)) {
        this.logout();
        return null;
      }

      return session;
    } catch {
      return null;
    }
  }

  static isAuthenticated(): boolean {
    const session = this.getCurrentSession();
    return session?.isAuthenticated ?? false;
  }

  private static generateSessionToken(): string {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
  }
}