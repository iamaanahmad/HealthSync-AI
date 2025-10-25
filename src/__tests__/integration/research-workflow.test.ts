/**
 * Integration tests for the complete research workflow
 * Tests the end-to-end flow from query submission to results viewing
 */

import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { fail } from 'assert';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';
import { ResearchQueryService, ResearchQuery } from '../../lib/research-query-api';

// Mock localStorage for testing
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('Research Workflow Integration', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe('Complete Research Query Workflow', () => {
    it('should handle complete workflow from submission to results', async () => {
      // Step 1: Submit a research query
      const testQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Integration Test Study',
        studyDescription: 'This is a comprehensive integration test study to validate the complete research workflow including query submission, processing, and results retrieval.',
        dataRequirements: {
          dataTypes: ['demographics', 'vital_signs', 'lab_results'],
          researchCategories: ['clinical_trials', 'outcomes_research'],
          minimumSampleSize: 500,
          dateRange: {
            startDate: '2023-01-01T00:00:00.000Z',
            endDate: '2023-12-31T23:59:59.999Z',
          },
          dataRetentionDays: 365,
        },
        inclusionCriteria: ['Age 18-65', 'Confirmed diagnosis', 'Informed consent'],
        exclusionCriteria: ['Pregnancy', 'Severe comorbidities'],
        ethicalApprovalId: 'IRB-2024-123456',
        privacyRequirements: {
          anonymizationMethods: ['k_anonymity', 'suppression'],
          enhancedAnonymization: true,
        },
      };

      const submitResult = await ResearchQueryService.submitQuery(testQuery);
      
      expect(submitResult.success).toBe(true);
      expect(submitResult.queryId).toBeDefined();
      
      const queryId = submitResult.queryId!;

      // Step 2: Check initial query status
      const initialStatus = ResearchQueryService.getQueryStatus(queryId);
      
      expect(initialStatus).toBeDefined();
      expect(initialStatus!.queryId).toBe(queryId);
      expect(initialStatus!.status).toBe('submitted');
      expect(initialStatus!.progress).toBe(10);

      // Step 3: Verify query appears in history
      const queryHistory = ResearchQueryService.getQueryResults('HMS-12345');
      
      expect(queryHistory).toHaveLength(1);
      expect(queryHistory[0].queryId).toBe(queryId);
      expect(queryHistory[0].studyTitle).toBe('Integration Test Study');

      // Step 4: Wait for processing to complete (simulate)
      await new Promise(resolve => setTimeout(resolve, 100));

      // Step 5: Check final status and results
      const finalStatus = ResearchQueryService.getQueryStatus(queryId);
      const finalResult = ResearchQueryService.getQueryResult(queryId);

      expect(finalStatus).toBeDefined();
      expect(finalResult).toBeDefined();
      expect(finalResult!.queryId).toBe(queryId);
      expect(finalResult!.researcherId).toBe('HMS-12345');
    });

    it('should handle multiple concurrent queries', async () => {
      const queries = [
        {
          studyTitle: 'Concurrent Study 1',
          dataTypes: ['demographics', 'vital_signs'],
          researchCategories: ['epidemiology'],
        },
        {
          studyTitle: 'Concurrent Study 2',
          dataTypes: ['lab_results', 'medications'],
          researchCategories: ['drug_safety'],
        },
        {
          studyTitle: 'Concurrent Study 3',
          dataTypes: ['diagnoses', 'procedures'],
          researchCategories: ['outcomes_research'],
        },
      ];

      const submissionPromises = queries.map(async (queryData) => {
        const fullQuery: ResearchQuery = {
          researcherId: 'HMS-12345',
          studyTitle: queryData.studyTitle,
          studyDescription: 'Concurrent test study for integration testing of multiple simultaneous research queries.',
          dataRequirements: {
            dataTypes: queryData.dataTypes,
            researchCategories: queryData.researchCategories,
            minimumSampleSize: 100,
          },
          ethicalApprovalId: 'IRB-2024-123456',
        };

        return ResearchQueryService.submitQuery(fullQuery);
      });

      const results = await Promise.all(submissionPromises);

      // Verify all queries were submitted successfully
      results.forEach((result, index) => {
        expect(result.success).toBe(true);
        expect(result.queryId).toBeDefined();
      });

      // Verify all queries appear in history
      const queryHistory = ResearchQueryService.getQueryResults('HMS-12345');
      expect(queryHistory).toHaveLength(3);

      // Verify each query has correct data
      queries.forEach((queryData, index) => {
        const historyEntry = queryHistory.find(q => q.studyTitle === queryData.studyTitle);
        expect(historyEntry).toBeDefined();
        expect(historyEntry!.researcherId).toBe('HMS-12345');
      });
    });

    it('should validate query data requirements', async () => {
      // Test with invalid ethical approval ID
      const invalidQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Invalid Query Test',
        studyDescription: 'Testing validation with invalid ethical approval ID format.',
        dataRequirements: {
          dataTypes: ['demographics'],
          researchCategories: ['clinical_trials'],
        },
        ethicalApprovalId: 'INVALID-FORMAT',
      };

      const result = await ResearchQueryService.submitQuery(invalidQuery);
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.error).toContain('Invalid ethical approval ID format');
    });

    it('should handle query templates correctly', () => {
      const templates = ResearchQueryService.getQueryTemplates();
      
      expect(templates).toBeDefined();
      expect(Array.isArray(templates)).toBe(true);
      expect(templates.length).toBeGreaterThan(0);

      // Verify template structure
      templates.forEach(template => {
        expect(template.templateId).toBeDefined();
        expect(template.name).toBeDefined();
        expect(template.description).toBeDefined();
        expect(template.category).toBeDefined();
        expect(template.template).toBeDefined();
        expect(template.template.studyTitle).toBeDefined();
        expect(template.template.studyDescription).toBeDefined();
        expect(template.template.dataRequirements).toBeDefined();
        expect(template.template.dataRequirements.dataTypes).toBeDefined();
        expect(template.template.dataRequirements.researchCategories).toBeDefined();
      });
    });

    it('should track query processing progress', async () => {
      const testQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Progress Tracking Test',
        studyDescription: 'Testing query processing progress tracking through different stages.',
        dataRequirements: {
          dataTypes: ['demographics', 'vital_signs'],
          researchCategories: ['clinical_trials'],
          minimumSampleSize: 200,
        },
        ethicalApprovalId: 'IRB-2024-123456',
      };

      const submitResult = await ResearchQueryService.submitQuery(testQuery);
      expect(submitResult.success).toBe(true);
      
      const queryId = submitResult.queryId!;

      // Check initial progress
      const initialStatus = ResearchQueryService.getQueryStatus(queryId);
      expect(initialStatus!.progress).toBe(10);
      expect(initialStatus!.status).toBe('submitted');

      // Verify processing log exists
      const queryResult = ResearchQueryService.getQueryResult(queryId);
      expect(queryResult!.processingLog).toBeDefined();
      expect(queryResult!.processingLog.length).toBeGreaterThan(0);
      
      const firstLogEntry = queryResult!.processingLog[0];
      expect(firstLogEntry.action).toBe('Query Submitted');
      expect(firstLogEntry.agent).toBe('Research Query Agent');
      expect(firstLogEntry.details).toContain('queued for processing');
    });

    it('should handle researcher authentication correctly', () => {
      const researcher = ResearchQueryService.getCurrentResearcher();
      
      expect(researcher).toBeDefined();
      expect(researcher.researcherId).toBe('HMS-12345');
      expect(researcher.name).toBe('Dr. Sarah Chen');
      expect(researcher.institution).toBe('Harvard Medical School');
      expect(researcher.department).toBe('Epidemiology');
      expect(researcher.email).toBe('sarah.chen@hms.harvard.edu');
    });

    it('should validate data type and research category selections', async () => {
      // Test with valid selections
      const validQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Valid Selection Test',
        studyDescription: 'Testing valid data type and research category selections.',
        dataRequirements: {
          dataTypes: ['demographics', 'vital_signs', 'lab_results'],
          researchCategories: ['clinical_trials', 'outcomes_research'],
          minimumSampleSize: 100,
        },
        ethicalApprovalId: 'IRB-2024-123456',
      };

      const validResult = await ResearchQueryService.submitQuery(validQuery);
      expect(validResult.success).toBe(true);

      // Test with empty selections
      const emptyQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Empty Selection Test',
        studyDescription: 'Testing empty data type and research category selections.',
        dataRequirements: {
          dataTypes: [],
          researchCategories: [],
        },
        ethicalApprovalId: 'IRB-2024-123456',
      };

      const emptyResult = await ResearchQueryService.submitQuery(emptyQuery);
      expect(emptyResult.success).toBe(false);
      expect(emptyResult.error).toContain('At least one data type must be selected');
    });

    it('should handle privacy requirements correctly', async () => {
      const privacyQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Privacy Requirements Test',
        studyDescription: 'Testing privacy requirements and anonymization settings.',
        dataRequirements: {
          dataTypes: ['genomics', 'behavioral'],
          researchCategories: ['precision_medicine'],
          minimumSampleSize: 50,
          dataRetentionDays: 1825, // 5 years
        },
        ethicalApprovalId: 'IRB-2024-123456',
        privacyRequirements: {
          anonymizationMethods: ['k_anonymity', 'differential_privacy', 'l_diversity'],
          enhancedAnonymization: true,
        },
      };

      const result = await ResearchQueryService.submitQuery(privacyQuery);
      expect(result.success).toBe(true);

      const queryResult = ResearchQueryService.getQueryResult(result.queryId!);
      expect(queryResult).toBeDefined();
      
      // Verify privacy settings are preserved
      expect(queryResult!.datasetSummary.anonymizationMethods).toContain('k_anonymity');
      expect(queryResult!.datasetSummary.privacyMetrics.kAnonymity).toBeGreaterThanOrEqual(5);
    });

    it('should enforce data retention limits', async () => {
      const longRetentionQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Long Retention Test',
        studyDescription: 'Testing data retention period validation with a comprehensive study description that meets the minimum character requirements.',
        dataRequirements: {
          dataTypes: ['demographics'],
          researchCategories: ['clinical_trials'],
          dataRetentionDays: 3000, // Exceeds 7-year limit
        },
        ethicalApprovalId: 'IRB-2024-123456',
      };

      const result = await ResearchQueryService.submitQuery(longRetentionQuery);
      expect(result.success).toBe(false);
      expect(result.error).toContain('Data retention cannot exceed 7 years');
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle network simulation errors gracefully', async () => {
      // Mock a network error scenario
      const originalSubmit = ResearchQueryService.submitQuery;
      
      // Temporarily replace with error-throwing version
      ResearchQueryService.submitQuery = jest.fn().mockRejectedValue(new Error('Network error'));

      const testQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Network Error Test',
        studyDescription: 'Testing network error handling.',
        dataRequirements: {
          dataTypes: ['demographics'],
          researchCategories: ['clinical_trials'],
        },
        ethicalApprovalId: 'IRB-2024-123456',
      };

      try {
        await ResearchQueryService.submitQuery(testQuery);
        fail('Expected error to be thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toBe('Network error');
      }

      // Restore original function
      ResearchQueryService.submitQuery = originalSubmit;
    });

    it('should handle missing query results gracefully', () => {
      const nonExistentQueryId = 'NON-EXISTENT-QUERY-ID';
      
      const status = ResearchQueryService.getQueryStatus(nonExistentQueryId);
      const result = ResearchQueryService.getQueryResult(nonExistentQueryId);
      
      expect(status).toBeNull();
      expect(result).toBeNull();
    });

    it('should handle empty researcher query history', () => {
      const nonExistentResearcher = 'NON-EXISTENT-RESEARCHER';
      
      const history = ResearchQueryService.getQueryResults(nonExistentResearcher);
      
      expect(history).toBeDefined();
      expect(Array.isArray(history)).toBe(true);
      expect(history).toHaveLength(0);
    });
  });

  describe('Performance and Scalability', () => {
    it('should handle large query descriptions', async () => {
      const largeDescription = 'A'.repeat(5000); // 5KB description
      
      const largeQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Large Description Test',
        studyDescription: largeDescription,
        dataRequirements: {
          dataTypes: ['demographics'],
          researchCategories: ['clinical_trials'],
        },
        ethicalApprovalId: 'IRB-2024-123456',
      };

      const result = await ResearchQueryService.submitQuery(largeQuery);
      expect(result.success).toBe(true);
    });

    it('should handle multiple data types and categories', async () => {
      const comprehensiveQuery: ResearchQuery = {
        researcherId: 'HMS-12345',
        studyTitle: 'Comprehensive Data Test',
        studyDescription: 'Testing with all available data types and research categories.',
        dataRequirements: {
          dataTypes: [
            'demographics', 'vital_signs', 'lab_results', 'medications',
            'diagnoses', 'procedures', 'imaging', 'behavioral',
            'social_determinants', 'clinical_notes', 'device_data'
          ],
          researchCategories: [
            'clinical_trials', 'epidemiology', 'public_health', 'drug_safety',
            'outcomes_research', 'health_economics', 'quality_improvement',
            'population_health', 'precision_medicine', 'digital_health'
          ],
          minimumSampleSize: 1000,
        },
        inclusionCriteria: [
          'Age 18-85', 'Confirmed diagnosis', 'Informed consent',
          'Complete medical records', 'Follow-up data available'
        ],
        exclusionCriteria: [
          'Pregnancy', 'Severe comorbidities', 'Incomplete records',
          'Previous study participation', 'Cognitive impairment'
        ],
        ethicalApprovalId: 'IRB-2024-123456',
        privacyRequirements: {
          anonymizationMethods: ['k_anonymity', 'suppression', 'generalization'],
          enhancedAnonymization: true,
        },
      };

      const result = await ResearchQueryService.submitQuery(comprehensiveQuery);
      expect(result.success).toBe(true);
      
      const queryResult = ResearchQueryService.getQueryResult(result.queryId!);
      expect(queryResult!.datasetSummary.dataTypes).toHaveLength(11);
    });
  });
});