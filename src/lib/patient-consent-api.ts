// API client for communicating with Patient Consent Agent
import { z } from 'zod';

// Consent data types and research categories
export const DataTypes = {
  GENOMIC: 'genomic_data',
  CLINICAL_TRIALS: 'clinical_trials',
  IMAGING: 'imaging_data',
  HEALTH_RECORDS: 'health_records',
  WEARABLE: 'wearable_data',
  LABORATORY: 'laboratory_results',
  MEDICATIONS: 'medication_history',
} as const;

export const ResearchCategories = {
  CANCER_RESEARCH: 'cancer_research',
  CARDIOVASCULAR: 'cardiovascular_research',
  DIABETES: 'diabetes_research',
  MENTAL_HEALTH: 'mental_health_research',
  INFECTIOUS_DISEASE: 'infectious_disease_research',
  RARE_DISEASES: 'rare_disease_research',
  DRUG_DEVELOPMENT: 'drug_development',
  POPULATION_HEALTH: 'population_health',
} as const;

export type DataType = typeof DataTypes[keyof typeof DataTypes];
export type ResearchCategory = typeof ResearchCategories[keyof typeof ResearchCategories];

// Consent record schema
export const ConsentRecordSchema = z.object({
  consentId: z.string(),
  patientId: z.string(),
  dataType: z.string(),
  researchCategory: z.string(),
  consentGranted: z.boolean(),
  expiryDate: z.string(),
  lastUpdated: z.string(),
  version: z.number(),
});

export type ConsentRecord = z.infer<typeof ConsentRecordSchema>;

// Consent update request
export const ConsentUpdateSchema = z.object({
  patientId: z.string(),
  dataType: z.string(),
  researchCategory: z.string(),
  consentGranted: z.boolean(),
  expiryDate: z.string().optional(),
});

export type ConsentUpdate = z.infer<typeof ConsentUpdateSchema>;

// API response types
export interface ConsentApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

// Patient Consent Agent API client
export class PatientConsentApi {
  private static readonly BASE_URL = process.env.NEXT_PUBLIC_CONSENT_AGENT_URL || 'http://localhost:8001';
  
  // Mock consent data for development
  private static mockConsentData: Record<string, ConsentRecord[]> = {
    'P001': [
      {
        consentId: 'C001-001',
        patientId: 'P001',
        dataType: DataTypes.GENOMIC,
        researchCategory: ResearchCategories.CANCER_RESEARCH,
        consentGranted: true,
        expiryDate: '2025-12-31',
        lastUpdated: '2024-12-10T10:00:00Z',
        version: 1,
      },
      {
        consentId: 'C001-002',
        patientId: 'P001',
        dataType: DataTypes.HEALTH_RECORDS,
        researchCategory: ResearchCategories.CARDIOVASCULAR,
        consentGranted: true,
        expiryDate: '2025-06-30',
        lastUpdated: '2024-12-10T10:00:00Z',
        version: 1,
      },
      {
        consentId: 'C001-003',
        patientId: 'P001',
        dataType: DataTypes.CLINICAL_TRIALS,
        researchCategory: ResearchCategories.DRUG_DEVELOPMENT,
        consentGranted: false,
        expiryDate: '2025-12-31',
        lastUpdated: '2024-12-10T10:00:00Z',
        version: 1,
      },
    ],
    'P002': [
      {
        consentId: 'C002-001',
        patientId: 'P002',
        dataType: DataTypes.WEARABLE,
        researchCategory: ResearchCategories.DIABETES,
        consentGranted: true,
        expiryDate: '2025-12-31',
        lastUpdated: '2024-12-10T10:00:00Z',
        version: 1,
      },
    ],
  };

  static async getPatientConsents(patientId: string): Promise<ConsentApiResponse<ConsentRecord[]>> {
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const consents = this.mockConsentData[patientId] || [];
      
      return {
        success: true,
        data: consents,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to fetch consent records',
        timestamp: new Date().toISOString(),
      };
    }
  }

  static async updateConsent(update: ConsentUpdate): Promise<ConsentApiResponse<ConsentRecord>> {
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const patientConsents = this.mockConsentData[update.patientId] || [];
      
      // Find existing consent record
      const existingIndex = patientConsents.findIndex(
        c => c.dataType === update.dataType && c.researchCategory === update.researchCategory
      );
      
      const newRecord: ConsentRecord = {
        consentId: existingIndex >= 0 ? patientConsents[existingIndex].consentId : `C${update.patientId}-${Date.now()}`,
        patientId: update.patientId,
        dataType: update.dataType,
        researchCategory: update.researchCategory,
        consentGranted: update.consentGranted,
        expiryDate: update.expiryDate || '2025-12-31',
        lastUpdated: new Date().toISOString(),
        version: existingIndex >= 0 ? patientConsents[existingIndex].version + 1 : 1,
      };
      
      if (existingIndex >= 0) {
        patientConsents[existingIndex] = newRecord;
      } else {
        patientConsents.push(newRecord);
      }
      
      this.mockConsentData[update.patientId] = patientConsents;
      
      return {
        success: true,
        data: newRecord,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to update consent',
        timestamp: new Date().toISOString(),
      };
    }
  }

  static async getConsentHistory(patientId: string, dataType?: string): Promise<ConsentApiResponse<ConsentRecord[]>> {
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 600));
      
      let consents = this.mockConsentData[patientId] || [];
      
      if (dataType) {
        consents = consents.filter(c => c.dataType === dataType);
      }
      
      // Sort by last updated (newest first)
      consents.sort((a, b) => new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime());
      
      return {
        success: true,
        data: consents,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to fetch consent history',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Check if consent is expiring soon (within 30 days)
  static isConsentExpiringSoon(consent: ConsentRecord): boolean {
    const expiryDate = new Date(consent.expiryDate);
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
    
    return expiryDate <= thirtyDaysFromNow;
  }

  // Get human-readable labels
  static getDataTypeLabel(dataType: string): string {
    const labels: Record<string, string> = {
      [DataTypes.GENOMIC]: 'Genomic Data',
      [DataTypes.CLINICAL_TRIALS]: 'Clinical Trials',
      [DataTypes.IMAGING]: 'Medical Imaging',
      [DataTypes.HEALTH_RECORDS]: 'Health Records',
      [DataTypes.WEARABLE]: 'Wearable Data',
      [DataTypes.LABORATORY]: 'Laboratory Results',
      [DataTypes.MEDICATIONS]: 'Medication History',
    };
    return labels[dataType] || dataType;
  }

  static getResearchCategoryLabel(category: string): string {
    const labels: Record<string, string> = {
      [ResearchCategories.CANCER_RESEARCH]: 'Cancer Research',
      [ResearchCategories.CARDIOVASCULAR]: 'Cardiovascular Research',
      [ResearchCategories.DIABETES]: 'Diabetes Research',
      [ResearchCategories.MENTAL_HEALTH]: 'Mental Health Research',
      [ResearchCategories.INFECTIOUS_DISEASE]: 'Infectious Disease Research',
      [ResearchCategories.RARE_DISEASES]: 'Rare Disease Research',
      [ResearchCategories.DRUG_DEVELOPMENT]: 'Drug Development',
      [ResearchCategories.POPULATION_HEALTH]: 'Population Health',
    };
    return labels[category] || category;
  }
}