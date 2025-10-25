import { PatientConsentApi, DataTypes, ResearchCategories } from '../../lib/patient-consent-api';

describe('PatientConsentApi', () => {
  describe('getPatientConsents', () => {
    it('should return consents for existing patient', async () => {
      const result = await PatientConsentApi.getPatientConsents('P001');
      
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(Array.isArray(result.data)).toBe(true);
      expect(result.data!.length).toBeGreaterThan(0);
    });

    it('should return empty array for non-existent patient', async () => {
      const result = await PatientConsentApi.getPatientConsents('NONEXISTENT');
      
      expect(result.success).toBe(true);
      expect(result.data).toEqual([]);
    });
  });

  describe('updateConsent', () => {
    it('should update existing consent record', async () => {
      const update = {
        patientId: 'P001',
        dataType: DataTypes.GENOMIC,
        researchCategory: ResearchCategories.CANCER_RESEARCH,
        consentGranted: false,
      };

      const result = await PatientConsentApi.updateConsent(update);
      
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.consentGranted).toBe(false);
      expect(result.data!.version).toBeGreaterThan(1);
    });

    it('should create new consent record for new combination', async () => {
      const update = {
        patientId: 'P001',
        dataType: DataTypes.LABORATORY,
        researchCategory: ResearchCategories.MENTAL_HEALTH,
        consentGranted: true,
      };

      const result = await PatientConsentApi.updateConsent(update);
      
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data!.consentGranted).toBe(true);
      expect(result.data!.version).toBe(1);
    });
  });

  describe('getConsentHistory', () => {
    it('should return consent history for patient', async () => {
      const result = await PatientConsentApi.getConsentHistory('P001');
      
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(Array.isArray(result.data)).toBe(true);
    });

    it('should filter by data type when provided', async () => {
      const result = await PatientConsentApi.getConsentHistory('P001', DataTypes.GENOMIC);
      
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      
      if (result.data!.length > 0) {
        expect(result.data!.every(c => c.dataType === DataTypes.GENOMIC)).toBe(true);
      }
    });
  });

  describe('utility functions', () => {
    it('should detect expiring consent', () => {
      const soonExpiring = {
        consentId: 'test',
        patientId: 'P001',
        dataType: DataTypes.GENOMIC,
        researchCategory: ResearchCategories.CANCER_RESEARCH,
        consentGranted: true,
        expiryDate: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(), // 15 days
        lastUpdated: new Date().toISOString(),
        version: 1,
      };

      const notExpiring = {
        ...soonExpiring,
        expiryDate: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(), // 60 days
      };

      expect(PatientConsentApi.isConsentExpiringSoon(soonExpiring)).toBe(true);
      expect(PatientConsentApi.isConsentExpiringSoon(notExpiring)).toBe(false);
    });

    it('should provide human-readable labels', () => {
      expect(PatientConsentApi.getDataTypeLabel(DataTypes.GENOMIC)).toBe('Genomic Data');
      expect(PatientConsentApi.getResearchCategoryLabel(ResearchCategories.CANCER_RESEARCH)).toBe('Cancer Research');
    });
  });
});