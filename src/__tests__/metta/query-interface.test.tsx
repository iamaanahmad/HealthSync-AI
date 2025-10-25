import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryInterface } from '@/components/metta/query-interface';
import { mettaAPI } from '@/lib/metta-api';

// Mock the MeTTa API
jest.mock('@/lib/metta-api');
const mockMettaAPI = mettaAPI as jest.Mocked<typeof mettaAPI>;

// Mock toast hook
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn()
  })
}));

describe('QueryInterface', () => {
  const mockOnQueryExecuted = jest.fn();
  
  const mockTemplates = [
    {
      id: 'consent_check',
      name: 'Check Patient Consent',
      description: 'Verify if a patient has valid consent',
      query_type: 'has_valid_consent',
      template: '(has-valid-consent ${patient_id} ${data_type_id} ${research_category_id})',
      parameters: [
        { name: 'patient_id', type: 'string', required: true, description: 'Patient identifier' },
        { name: 'data_type_id', type: 'string', required: true, description: 'Data type identifier' },
        { name: 'research_category_id', type: 'string', required: true, description: 'Research category identifier' }
      ],
      example_values: {
        patient_id: 'P001',
        data_type_id: 'DT001',
        research_category_id: 'RC001'
      }
    }
  ];

  const mockQueryResponse = {
    query_id: 'test_query_123',
    results: [{ consent_id: 'C001', valid: true }],
    reasoning_path: ['Checking consent for patient P001', 'Consent is valid'],
    confidence_score: 1.0,
    timestamp: '2024-01-01T00:00:00Z'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockMettaAPI.getQueryTemplates.mockResolvedValue(mockTemplates);
    mockMettaAPI.validateQuery.mockResolvedValue({ valid: true });
    mockMettaAPI.executeQuery.mockResolvedValue(mockQueryResponse);
  });

  it('should render query editor interface', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    expect(screen.getByText('Query Editor')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your MeTTa query expression...')).toBeInTheDocument();
    expect(screen.getByText('Execute Query')).toBeInTheDocument();
  });

  it('should load and display query templates', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    await waitFor(() => {
      expect(mockMettaAPI.getQueryTemplates).toHaveBeenCalled();
    });

    expect(screen.getByText('Query Templates')).toBeInTheDocument();
    expect(screen.getByText('Check Patient Consent')).toBeInTheDocument();
  });

  it('should load template when clicked', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Check Patient Consent')).toBeInTheDocument();
    });

    // Click on template
    fireEvent.click(screen.getByText('Check Patient Consent'));

    // Should load template into editor
    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    expect(queryTextarea).toHaveValue(mockTemplates[0].template);
  });

  it('should validate query as user types', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    
    // Type a query
    fireEvent.change(queryTextarea, { 
      target: { value: '(has-valid-consent P001 DT001 RC001)' } 
    });

    // Should validate after delay
    await waitFor(() => {
      expect(mockMettaAPI.validateQuery).toHaveBeenCalledWith('(has-valid-consent P001 DT001 RC001)');
    }, { timeout: 1000 });

    // Should show validation status
    expect(screen.getByText('Valid')).toBeInTheDocument();
  });

  it('should show validation errors for invalid queries', async () => {
    mockMettaAPI.validateQuery.mockResolvedValue({
      valid: false,
      errors: ['Query must be a valid MeTTa expression with parentheses']
    });

    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    
    fireEvent.change(queryTextarea, { target: { value: 'invalid query' } });

    await waitFor(() => {
      expect(screen.getByText('Invalid')).toBeInTheDocument();
      expect(screen.getByText('• Query must be a valid MeTTa expression with parentheses')).toBeInTheDocument();
    });
  });

  it('should execute query when button is clicked', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    const executeButton = screen.getByText('Execute Query');

    // Enter a valid query
    fireEvent.change(queryTextarea, { 
      target: { value: '(has-valid-consent P001 DT001 RC001)' } 
    });

    // Wait for validation
    await waitFor(() => {
      expect(screen.getByText('Valid')).toBeInTheDocument();
    });

    // Execute query
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(mockMettaAPI.executeQuery).toHaveBeenCalledWith({
        query_type: 'custom',
        query_expression: '(has-valid-consent P001 DT001 RC001)',
        context_variables: {}
      });
    });

    expect(mockOnQueryExecuted).toHaveBeenCalledWith(mockQueryResponse);
  });

  it('should show query results after execution', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    const executeButton = screen.getByText('Execute Query');

    fireEvent.change(queryTextarea, { 
      target: { value: '(has-valid-consent P001 DT001 RC001)' } 
    });

    await waitFor(() => {
      expect(screen.getByText('Valid')).toBeInTheDocument();
    });

    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByText('Query Results')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 100.0%')).toBeInTheDocument();
      expect(screen.getByText('Results: 1')).toBeInTheDocument();
    });
  });

  it('should handle template parameters', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Check Patient Consent')).toBeInTheDocument();
    });

    // Click on template
    fireEvent.click(screen.getByText('Check Patient Consent'));

    // Should show parameter inputs
    expect(screen.getByText('Parameters')).toBeInTheDocument();
    expect(screen.getByLabelText('patient_id')).toBeInTheDocument();
    expect(screen.getByLabelText('data_type_id')).toBeInTheDocument();
    expect(screen.getByLabelText('research_category_id')).toBeInTheDocument();
  });

  it('should substitute template variables', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    await waitFor(() => {
      expect(screen.getByText('Check Patient Consent')).toBeInTheDocument();
    });

    // Click on template
    fireEvent.click(screen.getByText('Check Patient Consent'));

    // Parameters should be pre-filled with example values
    const patientIdInput = screen.getByLabelText('patient_id');
    expect(patientIdInput).toHaveValue('P001');

    // Change a parameter
    fireEvent.change(patientIdInput, { target: { value: 'P999' } });

    // Query should be updated with new value
    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    await waitFor(() => {
      expect(queryTextarea).toHaveValue('(has-valid-consent P999 DT001 RC001)');
    });
  });

  it('should maintain query history', async () => {
    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    const executeButton = screen.getByText('Execute Query');

    // Execute a query
    fireEvent.change(queryTextarea, { 
      target: { value: '(has-valid-consent P001 DT001 RC001)' } 
    });

    await waitFor(() => {
      expect(screen.getByText('Valid')).toBeInTheDocument();
    });

    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByText('Query History')).toBeInTheDocument();
    });

    // History should show the executed query
    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument(); // Confidence badge in history
    });
  });

  it('should prevent execution of invalid queries', async () => {
    mockMettaAPI.validateQuery.mockResolvedValue({
      valid: false,
      errors: ['Invalid syntax']
    });

    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    const executeButton = screen.getByText('Execute Query');

    fireEvent.change(queryTextarea, { target: { value: 'invalid' } });

    await waitFor(() => {
      expect(screen.getByText('Invalid')).toBeInTheDocument();
    });

    // Execute button should be disabled
    expect(executeButton).toBeDisabled();
  });

  it('should show loading state during query execution', async () => {
    // Mock delayed response
    mockMettaAPI.executeQuery.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockQueryResponse), 1000))
    );

    render(<QueryInterface onQueryExecuted={mockOnQueryExecuted} />);

    const queryTextarea = screen.getByPlaceholderText('Enter your MeTTa query expression...');
    const executeButton = screen.getByText('Execute Query');

    fireEvent.change(queryTextarea, { 
      target: { value: '(has-valid-consent P001 DT001 RC001)' } 
    });

    await waitFor(() => {
      expect(screen.getByText('Valid')).toBeInTheDocument();
    });

    fireEvent.click(executeButton);

    // Should show loading state
    expect(executeButton).toBeDisabled();
  });
});