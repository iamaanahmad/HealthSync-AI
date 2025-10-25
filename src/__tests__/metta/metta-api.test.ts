import { mettaAPI } from '@/lib/metta-api';

// Mock fetch for testing
global.fetch = jest.fn();

describe('MeTTa API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('executeQuery', () => {
    it('should execute a query successfully', async () => {
      const mockResponse = {
        query_id: 'test_query_123',
        results: [{ consent_id: 'C001', valid: true }],
        reasoning_path: ['Step 1', 'Step 2'],
        confidence_score: 1.0,
        timestamp: '2024-01-01T00:00:00Z'
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const query = {
        query_type: 'has_valid_consent',
        query_expression: '(has-valid-consent P001 DT001 RC001)',
        context_variables: {
          patient_id: 'P001',
          data_type_id: 'DT001',
          research_category_id: 'RC001'
        }
      };

      const result = await mettaAPI.executeQuery(query);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metta/query'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(query)
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('should handle query execution errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request'
      });

      const query = {
        query_type: 'invalid_query',
        query_expression: 'invalid syntax'
      };

      await expect(mettaAPI.executeQuery(query)).rejects.toThrow('Query failed: Bad Request');
    });
  });

  describe('getKnowledgeGraphStats', () => {
    it('should fetch knowledge graph statistics', async () => {
      const mockStats = {
        total_entities: 156,
        total_relationships: 89,
        entities_by_type: {
          'Patient': 25,
          'ConsentRecord': 45,
          'DataType': 4
        }
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

      const result = await mettaAPI.getKnowledgeGraphStats();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metta/stats/knowledge-graph')
      );
      expect(result).toEqual(mockStats);
    });
  });

  describe('getEntitySchemas', () => {
    it('should fetch entity schemas', async () => {
      const mockSchemas = [
        {
          entity_type: 'Patient',
          fields: [
            { name: 'patient_id', type: 'string', required: true },
            { name: 'active_status', type: 'boolean', required: true }
          ],
          relationships: [
            { name: 'has_consent', target_type: 'ConsentRecord', cardinality: 'one-to-many' }
          ]
        }
      ];

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSchemas
      });

      const result = await mettaAPI.getEntitySchemas();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metta/schema/entities')
      );
      expect(result).toEqual(mockSchemas);
    });
  });

  describe('validateQuery', () => {
    it('should validate a correct query', async () => {
      const mockValidation = { valid: true };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockValidation
      });

      const result = await mettaAPI.validateQuery('(has-valid-consent P001 DT001 RC001)');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metta/validate'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ query: '(has-valid-consent P001 DT001 RC001)' })
        })
      );
      expect(result).toEqual(mockValidation);
    });

    it('should return validation errors for invalid query', async () => {
      const mockValidation = {
        valid: false,
        errors: ['Query must be a valid MeTTa expression with parentheses']
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockValidation
      });

      const result = await mettaAPI.validateQuery('invalid query');

      expect(result).toEqual(mockValidation);
    });
  });

  describe('exportResults', () => {
    it('should export results as blob', async () => {
      const mockBlob = new Blob(['test data'], { type: 'application/json' });

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      });

      const result = await mettaAPI.exportResults('query_123', 'json');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metta/export/query_123?format=json')
      );
      expect(result).toEqual(mockBlob);
    });
  });

  describe('getQueryTemplates', () => {
    it('should fetch query templates', async () => {
      const mockTemplates = [
        {
          id: 'consent_check',
          name: 'Check Patient Consent',
          description: 'Verify if a patient has valid consent',
          query_type: 'has_valid_consent',
          template: '(has-valid-consent ${patient_id} ${data_type_id} ${research_category_id})',
          parameters: [
            { name: 'patient_id', type: 'string', required: true, description: 'Patient identifier' }
          ]
        }
      ];

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTemplates
      });

      const result = await mettaAPI.getQueryTemplates();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metta/templates')
      );
      expect(result).toEqual(mockTemplates);
    });
  });
});