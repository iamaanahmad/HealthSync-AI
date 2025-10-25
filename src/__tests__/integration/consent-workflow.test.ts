import { PatientConsentApi, DataTypes, ResearchCategories } from '../../lib/patient-consent-api';
import { AuthService } from '../../lib/auth';

// Mock localStorage for AuthService
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('Consent Management Workflow Integration', () => {
  const testPatientId = 'P001';
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock authenticated session
    const mockSession = {
      patientId: testPatientId,
      isAuthenticated: true,
      profile: {
        patientId: testPatientId,
        firstName: 'John',
        lastName: 'Doe',
        dateOfBirth: '1985-06-15',
        email: 'john.doe@email.com',
      },
      sessionToken: 'mock-token',
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
    };
    
    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockSession));
  });

  describe('Complete consent management workflow', () => {
    it('should handle full consent lifecycle', async () => {
      // 1. Load initial consents
      const initialResult = await PatientConsentApi.getPatientConsents(testPatientId);
      expect(initialResult.success).toBe(true);
      expect(Array.isArray(initialResult.data)).toBe(true);
      
      const initialConsents = initialResult.data!;
      const initialCount = initialConsents.length;

      // 2. Grant a new consent
      const newConsentUpdate = {
        patientId: testPatientId,
        dataType: DataTypes.LABORATORY,
        researchCategory: ResearchCategories.MENTAL_HEALTH,
        consentGranted: true,
      };

      const updateResult = await PatientConsentApi.updateConsent(newConsentUpdate);
      expect(updateResult.success).toBe(true);
      expect(updateResult.data).toBeDefined();
      expect(updateResult.data!.consentGranted).toBe(true);
      expect(updateResult.data!.version).toBe(1);

      // 3. Verify consent appears in patient consents
      const afterGrantResult = await PatientConsentApi.getPatientConsents(testPatientId);
      expect(afterGrantResult.success).toBe(true);
      expect(afterGrantResult.data!.length).toBe(initialCount + 1);
      
      const newConsent = afterGrantResult.data!.find(
        c => c.dataType === DataTypes.LABORATORY && c.researchCategory === ResearchCategories.MENTAL_HEALTH
      );
      expect(newConsent).toBeDefined();
      expect(newConsent!.consentGranted).toBe(true);

      // 4. Revoke the consent
      const revokeUpdate = {
        ...newConsentUpdate,
        consentGranted: false,
      };

      const revokeResult = await PatientConsentApi.updateConsent(revokeUpdate);
      expect(revokeResult.success).toBe(true);
      expect(revokeResult.data!.consentGranted).toBe(false);
      expect(revokeResult.data!.version).toBe(2); // Version should increment

      // 5. Verify consent history shows both changes
      const historyResult = await PatientConsentApi.getConsentHistory(testPatientId, DataTypes.LABORATORY);
      expect(historyResult.success).toBe(true);
      
      const labConsents = historyResult.data!.filter(
        c => c.dataType === DataTypes.LABORATORY && c.researchCategory === ResearchCategories.MENTAL_HEALTH
      );
      expect(labConsents.length).toBeGreaterThan(0);
      
      // Should have the latest version (revoked)
      const latestConsent = labConsents[0]; // History is sorted by lastUpdated desc
      expect(latestConsent.consentGranted).toBe(false);
      expect(latestConsent.version).toBe(2);
    });

    it('should handle multiple consent updates for same patient', async () => {
      const updates = [
        {
          patientId: testPatientId,
          dataType: DataTypes.GENOMIC,
          researchCategory: ResearchCategories.CANCER_RESEARCH,
          consentGranted: true,
        },
        {
          patientId: testPatientId,
          dataType: DataTypes.GENOMIC,
          researchCategory: ResearchCategories.RARE_DISEASES,
          consentGranted: true,
        },
        {
          patientId: testPatientId,
          dataType: DataTypes.WEARABLE,
          researchCategory: ResearchCategories.CARDIOVASCULAR,
          consentGranted: false,
        },
      ];

      // Apply all updates
      const results = await Promise.all(
        updates.map(update => PatientConsentApi.updateConsent(update))
      );

      // Verify all updates succeeded
      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.data).toBeDefined();
      });

      // Verify final state
      const finalConsents = await PatientConsentApi.getPatientConsents(testPatientId);
      expect(finalConsents.success).toBe(true);

      // Check each consent exists with correct value
      updates.forEach(update => {
        const consent = finalConsents.data!.find(
          c => c.dataType === update.dataType && c.researchCategory === update.researchCategory
        );
        expect(consent).toBeDefined();
        expect(consent!.consentGranted).toBe(update.consentGranted);
      });
    });

    it('should handle consent expiration detection', async () => {
      // Create a consent that expires soon
      const soonExpiringUpdate = {
        patientId: testPatientId,
        dataType: DataTypes.IMAGING,
        researchCategory: ResearchCategories.DRUG_DEVELOPMENT,
        consentGranted: true,
        expiryDate: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(), // 15 days
      };

      const updateResult = await PatientConsentApi.updateConsent(soonExpiringUpdate);
      expect(updateResult.success).toBe(true);

      // Verify expiration detection
      const consent = updateResult.data!;
      expect(PatientConsentApi.isConsentExpiringSoon(consent)).toBe(true);

      // Test with far future expiry
      const farFutureUpdate = {
        ...soonExpiringUpdate,
        expiryDate: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 year
      };

      const farFutureResult = await PatientConsentApi.updateConsent(farFutureUpdate);
      expect(farFutureResult.success).toBe(true);
      expect(PatientConsentApi.isConsentExpiringSoon(farFutureResult.data!)).toBe(false);
    });

    it('should handle consent filtering by data type', async () => {
      // Ensure we have consents for different data types
      const genomicUpdate = {
        patientId: testPatientId,
        dataType: DataTypes.GENOMIC,
        researchCategory: ResearchCategories.CANCER_RESEARCH,
        consentGranted: true,
      };

      const wearableUpdate = {
        patientId: testPatientId,
        dataType: DataTypes.WEARABLE,
        researchCategory: ResearchCategories.DIABETES,
        consentGranted: true,
      };

      await PatientConsentApi.updateConsent(genomicUpdate);
      await PatientConsentApi.updateConsent(wearableUpdate);

      // Test filtering by genomic data
      const genomicHistory = await PatientConsentApi.getConsentHistory(testPatientId, DataTypes.GENOMIC);
      expect(genomicHistory.success).toBe(true);
      
      if (genomicHistory.data!.length > 0) {
        genomicHistory.data!.forEach(consent => {
          expect(consent.dataType).toBe(DataTypes.GENOMIC);
        });
      }

      // Test filtering by wearable data
      const wearableHistory = await PatientConsentApi.getConsentHistory(testPatientId, DataTypes.WEARABLE);
      expect(wearableHistory.success).toBe(true);
      
      if (wearableHistory.data!.length > 0) {
        wearableHistory.data!.forEach(consent => {
          expect(consent.dataType).toBe(DataTypes.WEARABLE);
        });
      }

      // Test getting all consents (no filter)
      const allHistory = await PatientConsentApi.getConsentHistory(testPatientId);
      expect(allHistory.success).toBe(true);
      expect(allHistory.data!.length).toBeGreaterThanOrEqual(genomicHistory.data!.length + wearableHistory.data!.length);
    });
  });

  describe('Error handling and edge cases', () => {
    it('should handle non-existent patient gracefully', async () => {
      const nonExistentPatientId = 'NONEXISTENT';
      
      const consentsResult = await PatientConsentApi.getPatientConsents(nonExistentPatientId);
      expect(consentsResult.success).toBe(true);
      expect(consentsResult.data).toEqual([]);

      const historyResult = await PatientConsentApi.getConsentHistory(nonExistentPatientId);
      expect(historyResult.success).toBe(true);
      expect(historyResult.data).toEqual([]);
    });

    it('should handle invalid data types and categories', async () => {
      const invalidUpdate = {
        patientId: testPatientId,
        dataType: 'INVALID_DATA_TYPE',
        researchCategory: 'INVALID_CATEGORY',
        consentGranted: true,
      };

      // The API should still work (it's mock data), but in real implementation
      // this would be validated
      const result = await PatientConsentApi.updateConsent(invalidUpdate);
      expect(result.success).toBe(true);
    });

    it('should maintain consent versioning correctly', async () => {
      const baseUpdate = {
        patientId: testPatientId,
        dataType: DataTypes.MEDICATIONS,
        researchCategory: ResearchCategories.DRUG_DEVELOPMENT,
        consentGranted: true,
      };

      // First update
      const result1 = await PatientConsentApi.updateConsent(baseUpdate);
      expect(result1.success).toBe(true);
      expect(result1.data!.version).toBe(1);

      // Second update (toggle)
      const result2 = await PatientConsentApi.updateConsent({
        ...baseUpdate,
        consentGranted: false,
      });
      expect(result2.success).toBe(true);
      expect(result2.data!.version).toBe(2);

      // Third update (toggle back)
      const result3 = await PatientConsentApi.updateConsent({
        ...baseUpdate,
        consentGranted: true,
      });
      expect(result3.success).toBe(true);
      expect(result3.data!.version).toBe(3);
    });
  });

  describe('Utility functions', () => {
    it('should provide correct human-readable labels', () => {
      // Test data type labels
      expect(PatientConsentApi.getDataTypeLabel(DataTypes.GENOMIC)).toBe('Genomic Data');
      expect(PatientConsentApi.getDataTypeLabel(DataTypes.CLINICAL_TRIALS)).toBe('Clinical Trials');
      expect(PatientConsentApi.getDataTypeLabel(DataTypes.IMAGING)).toBe('Medical Imaging');

      // Test research category labels
      expect(PatientConsentApi.getResearchCategoryLabel(ResearchCategories.CANCER_RESEARCH)).toBe('Cancer Research');
      expect(PatientConsentApi.getResearchCategoryLabel(ResearchCategories.CARDIOVASCULAR)).toBe('Cardiovascular Research');
      expect(PatientConsentApi.getResearchCategoryLabel(ResearchCategories.DIABETES)).toBe('Diabetes Research');

      // Test unknown values
      expect(PatientConsentApi.getDataTypeLabel('unknown')).toBe('unknown');
      expect(PatientConsentApi.getResearchCategoryLabel('unknown')).toBe('unknown');
    });
  });
});