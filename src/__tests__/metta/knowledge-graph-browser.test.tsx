import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { KnowledgeGraphBrowser } from '@/components/metta/knowledge-graph-browser';
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

describe('KnowledgeGraphBrowser', () => {
  const mockOnEntitySelected = jest.fn();
  
  const mockStats = {
    total_entities: 156,
    total_relationships: 89,
    entities_by_type: {
      'Patient': 25,
      'ConsentRecord': 45,
      'DataType': 4,
      'ResearchCategory': 3
    }
  };

  const mockPatientEntities = [
    {
      patient_id: 'P001',
      demographic_hash: 'hash_abc123',
      created_at: '2024-01-15T10:30:00Z',
      active_status: true
    },
    {
      patient_id: 'P002',
      demographic_hash: 'hash_def456',
      created_at: '2024-01-16T14:20:00Z',
      active_status: true
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockMettaAPI.getKnowledgeGraphStats.mockResolvedValue(mockStats);
    mockMettaAPI.getEntitiesByType.mockResolvedValue(mockPatientEntities);
  });

  it('should render knowledge graph overview', async () => {
    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Knowledge Graph Overview')).toBeInTheDocument();
    });

    expect(screen.getByText('156')).toBeInTheDocument(); // Total entities
    expect(screen.getByText('89')).toBeInTheDocument(); // Total relationships
    expect(screen.getByText('4')).toBeInTheDocument(); // Entity types count
  });

  it('should load and display entity types', async () => {
    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    await waitFor(() => {
      expect(mockMettaAPI.getKnowledgeGraphStats).toHaveBeenCalled();
    });

    // Should show entity type selector
    expect(screen.getByText('Select entity type')).toBeInTheDocument();
  });

  it('should load entities when entity type is selected', async () => {
    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    await waitFor(() => {
      expect(mockMettaAPI.getEntitiesByType).toHaveBeenCalledWith('Patient');
    });

    // Should display patient entities
    await waitFor(() => {
      expect(screen.getByText('P001')).toBeInTheDocument();
      expect(screen.getByText('P002')).toBeInTheDocument();
    });
  });

  it('should handle entity selection', async () => {
    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('P001')).toBeInTheDocument();
    });

    // Click on first patient entity
    fireEvent.click(screen.getByText('P001'));

    expect(mockOnEntitySelected).toHaveBeenCalledWith('Patient', 'P001');
  });

  it('should filter entities based on search term', async () => {
    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('P001')).toBeInTheDocument();
      expect(screen.getByText('P002')).toBeInTheDocument();
    });

    // Search for specific patient
    const searchInput = screen.getByPlaceholderText('Search entities...');
    fireEvent.change(searchInput, { target: { value: 'P001' } });

    // Should show only matching entity
    expect(screen.getByText('P001')).toBeInTheDocument();
    expect(screen.queryByText('P002')).not.toBeInTheDocument();
  });

  it('should display entity details when selected', async () => {
    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
        selectedEntity="Patient:P001"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('P001')).toBeInTheDocument();
    });

    // Click on entity to show details
    fireEvent.click(screen.getByText('P001'));

    // Should show entity details panel
    expect(screen.getByText('Entity Details')).toBeInTheDocument();
    expect(screen.getByText('Properties')).toBeInTheDocument();
  });

  it('should handle refresh action', async () => {
    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    await waitFor(() => {
      expect(mockMettaAPI.getKnowledgeGraphStats).toHaveBeenCalledTimes(1);
    });

    // Click refresh button
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockMettaAPI.getKnowledgeGraphStats).toHaveBeenCalledTimes(2);
    });
  });

  it('should handle API errors gracefully', async () => {
    mockMettaAPI.getKnowledgeGraphStats.mockRejectedValue(new Error('API Error'));

    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    await waitFor(() => {
      expect(mockMettaAPI.getKnowledgeGraphStats).toHaveBeenCalled();
    });

    // Should still render the component structure
    expect(screen.getByText('Knowledge Graph Overview')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    // Mock a delayed response
    mockMettaAPI.getKnowledgeGraphStats.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockStats), 1000))
    );

    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    expect(screen.getByText('Loading statistics...')).toBeInTheDocument();
  });

  it('should display relationships for selected entity', async () => {
    render(
      <KnowledgeGraphBrowser 
        onEntitySelected={mockOnEntitySelected}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('P001')).toBeInTheDocument();
    });

    // Click on entity
    fireEvent.click(screen.getByText('P001'));

    // Should show relationships section
    await waitFor(() => {
      expect(screen.getByText('Relationships')).toBeInTheDocument();
    });
  });
});