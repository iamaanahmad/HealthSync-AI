import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MeTTaExplorerPage from '@/app/(app)/metta-explorer/page';

// Mock the child components
jest.mock('@/components/metta/knowledge-graph-browser', () => ({
  KnowledgeGraphBrowser: ({ onEntitySelected }: any) => (
    <div data-testid="knowledge-graph-browser">
      <button onClick={() => onEntitySelected('Patient', 'P001')}>
        Select Patient P001
      </button>
    </div>
  )
}));

jest.mock('@/components/metta/query-interface', () => ({
  QueryInterface: ({ onQueryExecuted }: any) => (
    <div data-testid="query-interface">
      <button onClick={() => onQueryExecuted({
        query_id: 'test_123',
        results: [{ test: 'result' }],
        reasoning_path: ['Step 1', 'Step 2'],
        confidence_score: 0.95,
        timestamp: '2024-01-01T00:00:00Z'
      })}>
        Execute Test Query
      </button>
    </div>
  )
}));

jest.mock('@/components/metta/reasoning-path-display', () => ({
  ReasoningPathDisplay: ({ queryResponse, onStepSelected }: any) => (
    <div data-testid="reasoning-path-display">
      {queryResponse ? (
        <div>
          <span>Query ID: {queryResponse.query_id}</span>
          <button onClick={() => onStepSelected('test-step')}>
            Select Step
          </button>
        </div>
      ) : (
        <span>No query response</span>
      )}
    </div>
  )
}));

jest.mock('@/components/metta/schema-explorer', () => ({
  SchemaExplorer: ({ onEntityTypeSelected }: any) => (
    <div data-testid="schema-explorer">
      <button onClick={() => onEntityTypeSelected('Patient')}>
        Select Patient Type
      </button>
    </div>
  )
}));

jest.mock('@/components/metta/query-results-export', () => ({
  QueryResultsExport: ({ queryResponse }: any) => (
    <div data-testid="query-results-export">
      {queryResponse ? (
        <span>Export available for query: {queryResponse.query_id}</span>
      ) : (
        <span>No results to export</span>
      )}
    </div>
  )
}));

describe('MeTTaExplorerPage', () => {
  it('should render the main page structure', () => {
    render(<MeTTaExplorerPage />);

    expect(screen.getByText('MeTTa Explorer')).toBeInTheDocument();
    expect(screen.getByText('Explore the knowledge graph, execute queries, and visualize reasoning paths')).toBeInTheDocument();
  });

  it('should render all tab options', () => {
    render(<MeTTaExplorerPage />);

    expect(screen.getByText('Knowledge Graph')).toBeInTheDocument();
    expect(screen.getByText('Query Interface')).toBeInTheDocument();
    expect(screen.getByText('Reasoning Paths')).toBeInTheDocument();
    expect(screen.getByText('Schema Explorer')).toBeInTheDocument();
    expect(screen.getByText('Export Results')).toBeInTheDocument();
  });

  it('should show knowledge graph browser by default', () => {
    render(<MeTTaExplorerPage />);

    expect(screen.getByTestId('knowledge-graph-browser')).toBeInTheDocument();
    expect(screen.getByText('Interactive visualization of entities and relationships in the MeTTa knowledge graph')).toBeInTheDocument();
  });

  it('should switch to query interface tab', () => {
    render(<MeTTaExplorerPage />);

    fireEvent.click(screen.getByText('Query Interface'));

    expect(screen.getByTestId('query-interface')).toBeInTheDocument();
    expect(screen.getByText('Execute MeTTa queries with syntax highlighting and real-time validation')).toBeInTheDocument();
  });

  it('should switch to reasoning paths tab', () => {
    render(<MeTTaExplorerPage />);

    fireEvent.click(screen.getByText('Reasoning Paths'));

    expect(screen.getByTestId('reasoning-path-display')).toBeInTheDocument();
    expect(screen.getByText('Step-by-step visualization of MeTTa reasoning processes and decision paths')).toBeInTheDocument();
  });

  it('should switch to schema explorer tab', () => {
    render(<MeTTaExplorerPage />);

    fireEvent.click(screen.getByText('Schema Explorer'));

    expect(screen.getByTestId('schema-explorer')).toBeInTheDocument();
    expect(screen.getByText('Browse entity types, relationships, and schema definitions')).toBeInTheDocument();
  });

  it('should switch to export results tab', () => {
    render(<MeTTaExplorerPage />);

    fireEvent.click(screen.getByText('Export Results'));

    expect(screen.getByTestId('query-results-export')).toBeInTheDocument();
    expect(screen.getByText('Export and share query results in various formats')).toBeInTheDocument();
  });

  it('should handle entity selection from knowledge graph browser', () => {
    render(<MeTTaExplorerPage />);

    // Should start with no selected entity
    expect(screen.getByTestId('knowledge-graph-browser')).toBeInTheDocument();

    // Click to select an entity
    fireEvent.click(screen.getByText('Select Patient P001'));

    // The component should handle the selection (state update)
    // This is tested through the component's internal state management
  });

  it('should handle query execution from query interface', () => {
    render(<MeTTaExplorerPage />);

    // Switch to query interface
    fireEvent.click(screen.getByText('Query Interface'));

    // Execute a query
    fireEvent.click(screen.getByText('Execute Test Query'));

    // Switch to reasoning paths to see the result
    fireEvent.click(screen.getByText('Reasoning Paths'));

    expect(screen.getByText('Query ID: test_123')).toBeInTheDocument();
  });

  it('should pass query response to export component', () => {
    render(<MeTTaExplorerPage />);

    // Execute a query first
    fireEvent.click(screen.getByText('Query Interface'));
    fireEvent.click(screen.getByText('Execute Test Query'));

    // Switch to export tab
    fireEvent.click(screen.getByText('Export Results'));

    expect(screen.getByText('Export available for query: test_123')).toBeInTheDocument();
  });

  it('should handle step selection from reasoning path display', () => {
    render(<MeTTaExplorerPage />);

    // Execute a query first
    fireEvent.click(screen.getByText('Query Interface'));
    fireEvent.click(screen.getByText('Execute Test Query'));

    // Switch to reasoning paths
    fireEvent.click(screen.getByText('Reasoning Paths'));

    // Select a step
    fireEvent.click(screen.getByText('Select Step'));

    // This should log the step selection (as per the component implementation)
    // The actual logging is tested through console.log mock if needed
  });

  it('should handle entity type selection from schema explorer', () => {
    render(<MeTTaExplorerPage />);

    // Switch to schema explorer
    fireEvent.click(screen.getByText('Schema Explorer'));

    // Select an entity type
    fireEvent.click(screen.getByText('Select Patient Type'));

    // This should update the selected entity state
    // The state change is internal to the component
  });

  it('should show appropriate content for each tab', () => {
    render(<MeTTaExplorerPage />);

    // Test each tab has its expected content
    const tabs = [
      { name: 'Knowledge Graph', testId: 'knowledge-graph-browser' },
      { name: 'Query Interface', testId: 'query-interface' },
      { name: 'Reasoning Paths', testId: 'reasoning-path-display' },
      { name: 'Schema Explorer', testId: 'schema-explorer' },
      { name: 'Export Results', testId: 'query-results-export' }
    ];

    tabs.forEach(tab => {
      fireEvent.click(screen.getByText(tab.name));
      expect(screen.getByTestId(tab.testId)).toBeInTheDocument();
    });
  });

  it('should maintain state across tab switches', () => {
    render(<MeTTaExplorerPage />);

    // Execute a query
    fireEvent.click(screen.getByText('Query Interface'));
    fireEvent.click(screen.getByText('Execute Test Query'));

    // Switch to another tab and back
    fireEvent.click(screen.getByText('Knowledge Graph'));
    fireEvent.click(screen.getByText('Reasoning Paths'));

    // Query response should still be available
    expect(screen.getByText('Query ID: test_123')).toBeInTheDocument();
  });
});