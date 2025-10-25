// Research Query API for researcher portal
import { z } from 'zod';

// Research query schemas based on the backend agent interface
export const ResearchQuerySchema = z.object({
  queryId: z.string().optional(),
  researcherId: z.string().min(1, 'Researcher ID is required'),
  studyTitle: z.string().min(1, 'Study title is required'),
  studyDescription: z.string().min(50, 'Study description must be at least 50 characters'),
  dataRequirements: z.object({
    dataTypes: z.array(z.string()).min(1, 'At least one data type must be selected'),
    researchCategories: z.array(z.string()).min(1, 'At least one research category must be selected'),
    minimumSampleSize: z.number().min(1, 'Minimum sample size must be at least 1').optional(),
    dateRange: z.object({
      startDate: z.string(),
      endDate: z.string(),
    }).optional(),
    specificFields: z.array(z.string()).optional(),
    longitudinalData: z.boolean().optional(),
    multiSiteData: z.boolean().optional(),
    dataRetentionDays: z.number().max(2555, 'Data retention cannot exceed 7 years').optional(),
  }),
  inclusionCriteria: z.array(z.string()).optional(),
  exclusionCriteria: z.array(z.string()).optional(),
  ethicalApprovalId: z.string().regex(/^(IRB|REB|EC)-\d{4}-\d{3,6}$/, 'Invalid ethical approval ID format'),
  privacyRequirements: z.object({
    anonymizationMethods: z.array(z.string()).optional(),
    enhancedAnonymization: z.boolean().optional(),
  }).optional(),
  studyDurationDays: z.number().optional(),
  metadata: z.record(z.any()).optional(),
});

export const QueryTemplateSchema = z.object({
  templateId: z.string(),
  name: z.string(),
  description: z.string(),
  category: z.string(),
  template: z.object({
    studyTitle: z.string(),
    studyDescription: z.string(),
    dataRequirements: z.object({
      dataTypes: z.array(z.string()),
      researchCategories: z.array(z.string()),
      minimumSampleSize: z.number().optional(),
    }),
    inclusionCriteria: z.array(z.string()).optional(),
    exclusionCriteria: z.array(z.string()).optional(),
  }),
});

export type ResearchQuery = z.infer<typeof ResearchQuerySchema>;
export type QueryTemplate = z.infer<typeof QueryTemplateSchema>;

// Query status and results
export interface QueryStatus {
  queryId: string;
  status: 'submitted' | 'validating' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number; // 0-100
  currentStep: string;
  estimatedTimeRemaining?: number; // seconds
  lastUpdated: Date;
  errorMessage?: string;
}

export interface QueryResult {
  queryId: string;
  researcherId: string;
  studyTitle: string;
  submittedAt: Date;
  completedAt?: Date;
  status: QueryStatus['status'];
  datasetSummary: {
    totalRecords: number;
    dataTypes: string[];
    dateRange: {
      startDate: string;
      endDate: string;
    };
    anonymizationMethods: string[];
    privacyMetrics: {
      kAnonymity: number;
      suppressionRate: number;
      generalizationLevel: string;
    };
  };
  anonymizedData?: Array<Record<string, any>>;
  processingLog: Array<{
    timestamp: Date;
    agent: string;
    action: string;
    details: string;
  }>;
  downloadUrl?: string;
  expiresAt?: Date;
}

// Available data types and research categories
export const AVAILABLE_DATA_TYPES = [
  { value: 'demographics', label: 'Demographics', description: 'Age, gender, ethnicity, etc.' },
  { value: 'vital_signs', label: 'Vital Signs', description: 'Blood pressure, heart rate, temperature' },
  { value: 'lab_results', label: 'Laboratory Results', description: 'Blood tests, urinalysis, etc.' },
  { value: 'medications', label: 'Medications', description: 'Prescriptions and dosages' },
  { value: 'diagnoses', label: 'Diagnoses', description: 'ICD codes and diagnostic information' },
  { value: 'procedures', label: 'Procedures', description: 'Medical procedures and interventions' },
  { value: 'imaging', label: 'Medical Imaging', description: 'X-rays, MRI, CT scans (metadata only)' },
  { value: 'genomics', label: 'Genomic Data', description: 'Genetic information (requires special approval)' },
  { value: 'behavioral', label: 'Behavioral Data', description: 'Mental health and behavioral assessments' },
  { value: 'social_determinants', label: 'Social Determinants', description: 'Social and economic factors' },
  { value: 'clinical_notes', label: 'Clinical Notes', description: 'Provider notes (anonymized)' },
  { value: 'device_data', label: 'Device Data', description: 'Wearable and monitoring device data' },
];

export const RESEARCH_CATEGORIES = [
  { value: 'clinical_trials', label: 'Clinical Trials', description: 'Interventional studies' },
  { value: 'epidemiology', label: 'Epidemiology', description: 'Disease patterns and causes' },
  { value: 'public_health', label: 'Public Health', description: 'Population health studies' },
  { value: 'drug_safety', label: 'Drug Safety', description: 'Medication safety and efficacy' },
  { value: 'outcomes_research', label: 'Outcomes Research', description: 'Treatment effectiveness' },
  { value: 'health_economics', label: 'Health Economics', description: 'Cost-effectiveness studies' },
  { value: 'quality_improvement', label: 'Quality Improvement', description: 'Healthcare quality initiatives' },
  { value: 'population_health', label: 'Population Health', description: 'Community health studies' },
  { value: 'precision_medicine', label: 'Precision Medicine', description: 'Personalized treatment approaches' },
  { value: 'digital_health', label: 'Digital Health', description: 'Technology-enabled healthcare' },
];

// Mock API service for research queries
export class ResearchQueryService {
  private static readonly STORAGE_KEY = 'healthsync_research_queries';
  private static readonly TEMPLATES_KEY = 'healthsync_query_templates';

  // Mock researcher authentication (in real app, this would be separate)
  static getCurrentResearcher() {
    return {
      researcherId: 'HMS-12345',
      name: 'Dr. Sarah Chen',
      institution: 'Harvard Medical School',
      department: 'Epidemiology',
      email: 'sarah.chen@hms.harvard.edu',
    };
  }

  // Submit a new research query
  static async submitQuery(query: ResearchQuery): Promise<{ success: boolean; queryId?: string; error?: string }> {
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Validate query
      const validatedQuery = ResearchQuerySchema.parse(query);
      
      // Generate query ID
      const queryId = `RQ-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
      
      // Create query result with initial status
      const queryResult: QueryResult = {
        queryId,
        researcherId: validatedQuery.researcherId,
        studyTitle: validatedQuery.studyTitle,
        submittedAt: new Date(),
        status: 'submitted',
        datasetSummary: {
          totalRecords: Math.floor(Math.random() * 500) + 100, // Generate immediate mock data for tests
          dataTypes: validatedQuery.dataRequirements.dataTypes,
          dateRange: validatedQuery.dataRequirements.dateRange || {
            startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
            endDate: new Date().toISOString(),
          },
          anonymizationMethods: validatedQuery.privacyRequirements?.anonymizationMethods || ['k_anonymity'],
          privacyMetrics: {
            kAnonymity: 5,
            suppressionRate: 0.02,
            generalizationLevel: 'medium',
          },
        },
        processingLog: [{
          timestamp: new Date(),
          agent: 'Research Query Agent',
          action: 'Query Submitted',
          details: 'Research query received and queued for processing',
        }],
      };

      // Store query
      this.storeQuery(queryResult);

      // Start mock processing
      this.simulateQueryProcessing(queryId);

      return { success: true, queryId };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return { success: false, error: error.errors[0].message };
      }
      return { success: false, error: 'Failed to submit query. Please try again.' };
    }
  }

  // Get query status
  static getQueryStatus(queryId: string): QueryStatus | null {
    const queries = this.getStoredQueries();
    const query = queries.find(q => q.queryId === queryId);
    
    if (!query) return null;

    return {
      queryId: query.queryId,
      status: query.status,
      progress: this.calculateProgress(query.status),
      currentStep: this.getCurrentStep(query.status),
      estimatedTimeRemaining: this.getEstimatedTime(query.status),
      lastUpdated: new Date(query.processingLog[query.processingLog.length - 1].timestamp),
      errorMessage: query.status === 'failed' ? 'Query processing failed due to validation errors' : undefined,
    };
  }

  // Get query results
  static getQueryResults(researcherId: string): QueryResult[] {
    return this.getStoredQueries().filter(q => q.researcherId === researcherId);
  }

  // Get specific query result
  static getQueryResult(queryId: string): QueryResult | null {
    const queries = this.getStoredQueries();
    return queries.find(q => q.queryId === queryId) || null;
  }

  // Get query templates
  static getQueryTemplates(): QueryTemplate[] {
    const stored = localStorage.getItem(this.TEMPLATES_KEY);
    if (stored) {
      return JSON.parse(stored);
    }

    // Default templates
    const defaultTemplates: QueryTemplate[] = [
      {
        templateId: 'clinical-trial-template',
        name: 'Clinical Trial Outcomes',
        description: 'Template for analyzing clinical trial effectiveness',
        category: 'Clinical Research',
        template: {
          studyTitle: 'Clinical Trial Outcomes Analysis',
          studyDescription: 'Analyzing the effectiveness and safety outcomes of clinical interventions in a controlled study population to evaluate treatment efficacy and identify potential adverse events.',
          dataRequirements: {
            dataTypes: ['demographics', 'vital_signs', 'lab_results', 'medications', 'procedures'],
            researchCategories: ['clinical_trials', 'outcomes_research'],
            minimumSampleSize: 100,
          },
          inclusionCriteria: ['Age 18-65', 'Confirmed diagnosis', 'Informed consent'],
          exclusionCriteria: ['Pregnancy', 'Severe comorbidities', 'Previous participation'],
        },
      },
      {
        templateId: 'epidemiology-template',
        name: 'Epidemiological Study',
        description: 'Template for population health and disease pattern analysis',
        category: 'Public Health',
        template: {
          studyTitle: 'Population Health Epidemiological Analysis',
          studyDescription: 'Investigating disease patterns, risk factors, and health outcomes in defined populations to understand the distribution and determinants of health conditions and inform public health interventions.',
          dataRequirements: {
            dataTypes: ['demographics', 'diagnoses', 'social_determinants', 'vital_signs'],
            researchCategories: ['epidemiology', 'public_health', 'population_health'],
            minimumSampleSize: 500,
          },
          inclusionCriteria: ['Geographic region', 'Age range', 'Data availability'],
          exclusionCriteria: ['Incomplete records', 'Duplicate entries'],
        },
      },
      {
        templateId: 'drug-safety-template',
        name: 'Drug Safety Analysis',
        description: 'Template for medication safety and adverse event monitoring',
        category: 'Pharmacovigilance',
        template: {
          studyTitle: 'Medication Safety and Adverse Event Analysis',
          studyDescription: 'Monitoring and analyzing medication safety profiles, adverse drug reactions, and drug-drug interactions to ensure patient safety and optimize therapeutic outcomes in real-world clinical settings.',
          dataRequirements: {
            dataTypes: ['medications', 'diagnoses', 'lab_results', 'demographics'],
            researchCategories: ['drug_safety', 'outcomes_research'],
            minimumSampleSize: 200,
          },
          inclusionCriteria: ['Medication exposure', 'Follow-up data', 'Adult patients'],
          exclusionCriteria: ['Pediatric patients', 'Missing medication data'],
        },
      },
    ];

    localStorage.setItem(this.TEMPLATES_KEY, JSON.stringify(defaultTemplates));
    return defaultTemplates;
  }

  // Private helper methods
  private static storeQuery(query: QueryResult): void {
    const queries = this.getStoredQueries();
    queries.push(query);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(queries));
  }

  private static getStoredQueries(): QueryResult[] {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  }

  private static updateQuery(queryId: string, updates: Partial<QueryResult>): void {
    const queries = this.getStoredQueries();
    const index = queries.findIndex(q => q.queryId === queryId);
    
    if (index !== -1) {
      queries[index] = { ...queries[index], ...updates };
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(queries));
    }
  }

  private static simulateQueryProcessing(queryId: string): void {
    const steps = [
      { status: 'validating' as const, delay: 2000, step: 'Validating query structure and ethical compliance' },
      { status: 'processing' as const, delay: 3000, step: 'Coordinating with data custodian agents' },
      { status: 'processing' as const, delay: 4000, step: 'Applying privacy and anonymization rules' },
      { status: 'completed' as const, delay: 2000, step: 'Finalizing anonymized dataset' },
    ];

    let currentIndex = 0;

    const processStep = () => {
      if (currentIndex >= steps.length) return;

      const step = steps[currentIndex];
      
      setTimeout(() => {
        this.updateQuery(queryId, {
          status: step.status,
          processingLog: [
            ...this.getQueryResult(queryId)?.processingLog || [],
            {
              timestamp: new Date(),
              agent: currentIndex < 2 ? 'Research Query Agent' : 'Privacy Agent',
              action: step.status === 'completed' ? 'Processing Complete' : 'Processing Step',
              details: step.step,
            },
          ],
        });

        // Add mock data for completed queries
        if (step.status === 'completed') {
          this.updateQuery(queryId, {
            completedAt: new Date(),
            datasetSummary: {
              ...this.getQueryResult(queryId)?.datasetSummary!,
              totalRecords: Math.floor(Math.random() * 1000) + 100,
            },
            downloadUrl: `https://api.healthsync.com/downloads/${queryId}`,
            expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
          });
        }

        currentIndex++;
        processStep();
      }, step.delay);
    };

    processStep();
  }

  private static calculateProgress(status: QueryStatus['status']): number {
    switch (status) {
      case 'submitted': return 10;
      case 'validating': return 25;
      case 'processing': return 60;
      case 'completed': return 100;
      case 'failed': return 0;
      case 'cancelled': return 0;
      default: return 0;
    }
  }

  private static getCurrentStep(status: QueryStatus['status']): string {
    switch (status) {
      case 'submitted': return 'Query submitted and queued';
      case 'validating': return 'Validating ethical compliance';
      case 'processing': return 'Processing data request';
      case 'completed': return 'Dataset ready for download';
      case 'failed': return 'Processing failed';
      case 'cancelled': return 'Query cancelled';
      default: return 'Unknown status';
    }
  }

  private static getEstimatedTime(status: QueryStatus['status']): number | undefined {
    switch (status) {
      case 'submitted': return 300; // 5 minutes
      case 'validating': return 180; // 3 minutes
      case 'processing': return 120; // 2 minutes
      default: return undefined;
    }
  }
}