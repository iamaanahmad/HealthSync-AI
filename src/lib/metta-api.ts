/**
 * MeTTa API for frontend integration
 * Provides interface to MeTTa Knowledge Graph operations
 */

export interface MeTTaQuery {
  query_id?: string;
  query_type: string;
  query_expression: string;
  context_variables?: Record<string, any>;
}

export interface MeTTaResponse {
  query_id: string;
  results: Array<Record<string, any>>;
  reasoning_path: string[];
  confidence_score: number;
  timestamp: string;
}

export interface KnowledgeGraphStats {
  total_entities: number;
  total_relationships: number;
  entities_by_type: Record<string, number>;
}

export interface ReasoningStats {
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  cache_hits: number;
  average_reasoning_time: number;
}

export interface EntitySchema {
  entity_type: string;
  fields: Array<{
    name: string;
    type: string;
    required: boolean;
    description?: string;
  }>;
  relationships: Array<{
    name: string;
    target_type: string;
    cardinality: string;
  }>;
}

export interface QueryTemplate {
  id: string;
  name: string;
  description: string;
  query_type: string;
  template: string;
  parameters: Array<{
    name: string;
    type: string;
    required: boolean;
    description: string;
  }>;
  example_values?: Record<string, any>;
}

class MeTTaAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';
  }

  /**
   * Execute a MeTTa query
   */
  async executeQuery(query: MeTTaQuery): Promise<MeTTaResponse> {
    const response = await fetch(`${this.baseUrl}/metta/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get knowledge graph statistics
   */
  async getKnowledgeGraphStats(): Promise<KnowledgeGraphStats> {
    const response = await fetch(`${this.baseUrl}/metta/stats/knowledge-graph`);
    
    if (!response.ok) {
      throw new Error(`Failed to get stats: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get reasoning statistics
   */
  async getReasoningStats(): Promise<ReasoningStats> {
    const response = await fetch(`${this.baseUrl}/metta/stats/reasoning`);
    
    if (!response.ok) {
      throw new Error(`Failed to get reasoning stats: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get entity schema information
   */
  async getEntitySchemas(): Promise<EntitySchema[]> {
    const response = await fetch(`${this.baseUrl}/metta/schema/entities`);
    
    if (!response.ok) {
      throw new Error(`Failed to get schemas: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get all entities of a specific type
   */
  async getEntitiesByType(entityType: string): Promise<Array<Record<string, any>>> {
    const response = await fetch(`${this.baseUrl}/metta/entities/${entityType}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get entities: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get query templates for common operations
   */
  async getQueryTemplates(): Promise<QueryTemplate[]> {
    const response = await fetch(`${this.baseUrl}/metta/templates`);
    
    if (!response.ok) {
      throw new Error(`Failed to get templates: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Validate a MeTTa query syntax
   */
  async validateQuery(query: string): Promise<{ valid: boolean; errors?: string[] }> {
    const response = await fetch(`${this.baseUrl}/metta/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Validation failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Export query results in various formats
   */
  async exportResults(
    queryId: string, 
    format: 'json' | 'csv' | 'xml'
  ): Promise<Blob> {
    const response = await fetch(
      `${this.baseUrl}/metta/export/${queryId}?format=${format}`
    );

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Get reasoning path visualization data
   */
  async getReasoningVisualization(queryId: string): Promise<{
    nodes: Array<{ id: string; label: string; type: string }>;
    edges: Array<{ source: string; target: string; label: string }>;
  }> {
    const response = await fetch(`${this.baseUrl}/metta/reasoning/${queryId}/visualization`);
    
    if (!response.ok) {
      throw new Error(`Failed to get visualization: ${response.statusText}`);
    }

    return response.json();
  }
}

// Mock implementation for development
class MockMeTTaAPI extends MeTTaAPI {
  async executeQuery(query: MeTTaQuery): Promise<MeTTaResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    const mockResults = this.generateMockResults(query.query_type);
    
    return {
      query_id: `query_${Date.now()}`,
      results: mockResults.results,
      reasoning_path: mockResults.reasoning_path,
      confidence_score: mockResults.confidence_score,
      timestamp: new Date().toISOString(),
    };
  }

  async getKnowledgeGraphStats(): Promise<KnowledgeGraphStats> {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return {
      total_entities: 156,
      total_relationships: 89,
      entities_by_type: {
        'Patient': 25,
        'ConsentRecord': 45,
        'DataType': 4,
        'ResearchCategory': 3,
        'PrivacyRule': 4,
        'AnonymizationMethod': 3,
      },
    };
  }

  async getReasoningStats(): Promise<ReasoningStats> {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return {
      total_queries: 1247,
      successful_queries: 1198,
      failed_queries: 49,
      cache_hits: 423,
      average_reasoning_time: 0.156,
    };
  }

  async getEntitySchemas(): Promise<EntitySchema[]> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    return [
      {
        entity_type: 'Patient',
        fields: [
          { name: 'patient_id', type: 'string', required: true, description: 'Unique patient identifier' },
          { name: 'demographic_hash', type: 'string', required: true, description: 'Hashed demographic data' },
          { name: 'created_at', type: 'datetime', required: true, description: 'Creation timestamp' },
          { name: 'active_status', type: 'boolean', required: true, description: 'Whether patient is active' },
        ],
        relationships: [
          { name: 'has_consent', target_type: 'ConsentRecord', cardinality: 'one-to-many' },
        ],
      },
      {
        entity_type: 'ConsentRecord',
        fields: [
          { name: 'consent_id', type: 'string', required: true, description: 'Unique consent identifier' },
          { name: 'patient_ref', type: 'string', required: true, description: 'Reference to patient' },
          { name: 'data_type_ref', type: 'string', required: true, description: 'Reference to data type' },
          { name: 'research_category_ref', type: 'string', required: true, description: 'Reference to research category' },
          { name: 'consent_granted', type: 'boolean', required: true, description: 'Whether consent is granted' },
          { name: 'expiry_date', type: 'datetime', required: true, description: 'Consent expiration date' },
          { name: 'last_updated', type: 'datetime', required: true, description: 'Last update timestamp' },
        ],
        relationships: [
          { name: 'belongs_to', target_type: 'Patient', cardinality: 'many-to-one' },
          { name: 'covers', target_type: 'DataType', cardinality: 'many-to-one' },
          { name: 'allows', target_type: 'ResearchCategory', cardinality: 'many-to-one' },
        ],
      },
      {
        entity_type: 'DataType',
        fields: [
          { name: 'type_id', type: 'string', required: true, description: 'Unique data type identifier' },
          { name: 'type_name', type: 'string', required: true, description: 'Human-readable name' },
          { name: 'sensitivity_level', type: 'string', required: true, description: 'Sensitivity classification' },
          { name: 'required_permissions', type: 'array', required: true, description: 'Required permissions list' },
        ],
        relationships: [
          { name: 'covered_by', target_type: 'ConsentRecord', cardinality: 'one-to-many' },
          { name: 'governed_by', target_type: 'PrivacyRule', cardinality: 'one-to-many' },
        ],
      },
    ];
  }

  async getEntitiesByType(entityType: string): Promise<Array<Record<string, any>>> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const mockEntities: Record<string, Array<Record<string, any>>> = {
      'Patient': [
        {
          patient_id: 'P001',
          demographic_hash: 'hash_abc123',
          created_at: '2024-01-15T10:30:00Z',
          active_status: true,
        },
        {
          patient_id: 'P002',
          demographic_hash: 'hash_def456',
          created_at: '2024-01-16T14:20:00Z',
          active_status: true,
        },
      ],
      'DataType': [
        {
          type_id: 'DT001',
          type_name: 'Medical Records',
          sensitivity_level: 'high',
          required_permissions: ['patient_consent', 'ethics_approval'],
        },
        {
          type_id: 'DT002',
          type_name: 'Lab Results',
          sensitivity_level: 'high',
          required_permissions: ['patient_consent', 'ethics_approval'],
        },
      ],
    };

    return mockEntities[entityType] || [];
  }

  async getQueryTemplates(): Promise<QueryTemplate[]> {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return [
      {
        id: 'consent_check',
        name: 'Check Patient Consent',
        description: 'Verify if a patient has valid consent for specific data type and research',
        query_type: 'has_valid_consent',
        template: '(has-valid-consent ${patient_id} ${data_type_id} ${research_category_id})',
        parameters: [
          { name: 'patient_id', type: 'string', required: true, description: 'Patient identifier' },
          { name: 'data_type_id', type: 'string', required: true, description: 'Data type identifier' },
          { name: 'research_category_id', type: 'string', required: true, description: 'Research category identifier' },
        ],
        example_values: {
          patient_id: 'P001',
          data_type_id: 'DT001',
          research_category_id: 'RC001',
        },
      },
      {
        id: 'privacy_rule',
        name: 'Get Privacy Rule',
        description: 'Retrieve privacy rule for a specific data type',
        query_type: 'get_privacy_rule',
        template: '(get-privacy-rule ${data_type_id})',
        parameters: [
          { name: 'data_type_id', type: 'string', required: true, description: 'Data type identifier' },
        ],
        example_values: {
          data_type_id: 'DT001',
        },
      },
    ];
  }

  async validateQuery(query: string): Promise<{ valid: boolean; errors?: string[] }> {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Simple validation logic
    if (!query.trim()) {
      return { valid: false, errors: ['Query cannot be empty'] };
    }
    
    if (!query.includes('(') || !query.includes(')')) {
      return { valid: false, errors: ['Query must be a valid MeTTa expression with parentheses'] };
    }
    
    return { valid: true };
  }

  async exportResults(queryId: string, format: 'json' | 'csv' | 'xml'): Promise<Blob> {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const mockData = {
      query_id: queryId,
      results: [{ id: 1, value: 'mock_result' }],
      exported_at: new Date().toISOString(),
    };
    
    let content: string;
    let mimeType: string;
    
    switch (format) {
      case 'json':
        content = JSON.stringify(mockData, null, 2);
        mimeType = 'application/json';
        break;
      case 'csv':
        content = 'id,value\n1,mock_result';
        mimeType = 'text/csv';
        break;
      case 'xml':
        content = `<?xml version="1.0"?><results><item id="1" value="mock_result"/></results>`;
        mimeType = 'application/xml';
        break;
    }
    
    return new Blob([content], { type: mimeType });
  }

  async getReasoningVisualization(queryId: string) {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    return {
      nodes: [
        { id: 'start', label: 'Query Start', type: 'start' },
        { id: 'consent_check', label: 'Check Consent', type: 'process' },
        { id: 'validation', label: 'Validate Rules', type: 'process' },
        { id: 'result', label: 'Query Result', type: 'end' },
      ],
      edges: [
        { source: 'start', target: 'consent_check', label: 'initiate' },
        { source: 'consent_check', target: 'validation', label: 'valid' },
        { source: 'validation', target: 'result', label: 'approved' },
      ],
    };
  }

  private generateMockResults(queryType: string) {
    const mockResults: Record<string, any> = {
      'has_valid_consent': {
        results: [{ consent_id: 'C001', valid: true, expiry_date: '2024-12-31T23:59:59Z' }],
        reasoning_path: [
          'Checking consent for patient P001',
          'Data type: DT001, Research: RC001',
          'Found consent record: C001',
          'Consent is granted',
          'Consent is valid and not expired',
        ],
        confidence_score: 1.0,
      },
      'get_privacy_rule': {
        results: [{
          rule_id: 'PR001',
          rule_name: 'High Sensitivity Rule',
          k_anonymity_threshold: 5,
          anonymization_method: { method_name: 'K-Anonymity', technique: 'generalization' },
        }],
        reasoning_path: [
          'Finding privacy rule for data type: DT001',
          'Found privacy rule: PR001',
          'Anonymization method: K-Anonymity',
        ],
        confidence_score: 1.0,
      },
    };

    return mockResults[queryType] || {
      results: [],
      reasoning_path: ['Unknown query type'],
      confidence_score: 0.0,
    };
  }
}

// Export the appropriate implementation
export const mettaAPI = process.env.NODE_ENV === 'development' 
  ? new MockMeTTaAPI() 
  : new MeTTaAPI();

export default mettaAPI;