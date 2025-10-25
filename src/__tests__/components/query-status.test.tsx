import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryStatusTracker } from '../../components/researcher/query-status';
import { ResearchQueryService } from '../../lib/research-query-api';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock the ResearchQueryService
jest.mock('../../lib/research-query-api', () => ({
  ResearchQueryService: {
    getQueryStatus: jest.fn(),
    getQueryResult: jest.fn(),
  },
}));

// Mock UI components
jest.mock('../../components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  CardDescription: ({ children }: any) => <div data-testid="card-description">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <h3 data-testid="card-title">{children}</h3>,
}));

jest.mock('../../components/ui/badge', () => ({
  Badge: ({ children, className }: any) => (
    <span data-testid="badge" className={className}>{children}</span>
  ),
}));

jest.mock('../../components/ui/progress', () => ({
  Progress: ({ value }: any) => (
    <div data-testid="progress" data-value={value}>
      Progress: {value}%
    </div>
  ),
}));

jest.mock('../../components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, size, asChild, ...props }: any) => {
    if (asChild) {
      return <div data-testid="button-wrapper">{children}</div>;
    }
    return (
      <button 
        onClick={onClick} 
        disabled={disabled} 
        data-testid="button"
        data-variant={variant}
        data-size={size}
        {...props}
      >
        {children}
      </button>
    );
  },
}));

jest.mock('../../components/ui/separator', () => ({
  Separator: () => <hr data-testid="separator" />,
}));

jest.mock('../../components/ui/scroll-area', () => ({
  ScrollArea: ({ children }: any) => <div data-testid="scroll-area">{children}</div>,
}));

jest.mock('../../components/ui/alert', () => ({
  Alert: ({ children, variant }: any) => (
    <div data-testid="alert" data-variant={variant}>{children}</div>
  ),
  AlertDescription: ({ children }: any) => <div data-testid="alert-description">{children}</div>,
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Clock: () => <span data-testid="clock-icon">🕐</span>,
  CheckCircle: () => <span data-testid="check-circle-icon">✅</span>,
  XCircle: () => <span data-testid="x-circle-icon">❌</span>,
  AlertCircle: () => <span data-testid="alert-circle-icon">⚠️</span>,
  Download: () => <span data-testid="download-icon">⬇️</span>,
  Eye: () => <span data-testid="eye-icon">👁️</span>,
  RefreshCw: () => <span data-testid="refresh-icon">🔄</span>,
  Calendar: () => <span data-testid="calendar-icon">📅</span>,
  User: () => <span data-testid="user-icon">👤</span>,
  Database: () => <span data-testid="database-icon">🗄️</span>,
  Shield: () => <span data-testid="shield-icon">🛡️</span>,
  Activity: () => <span data-testid="activity-icon">📊</span>,
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  format: (date: Date | string, formatStr: string) => {
    const d = new Date(date);
    if (formatStr === 'PPP') return d.toLocaleDateString();
    if (formatStr === 'HH:mm:ss') return d.toLocaleTimeString();
    return d.toLocaleDateString();
  },
  formatDistanceToNow: (date: Date | string) => {
    return '2 hours ago';
  },
}));

describe('QueryStatusTracker', () => {
  const mockGetQueryStatus = ResearchQueryService.getQueryStatus as jest.MockedFunction<typeof ResearchQueryService.getQueryStatus>;
  const mockGetQueryResult = ResearchQueryService.getQueryResult as jest.MockedFunction<typeof ResearchQueryService.getQueryResult>;
  const mockOnViewResults = jest.fn();

  const mockQueryStatus = {
    queryId: 'test-query-id',
    status: 'processing' as const,
    progress: 60,
    currentStep: 'Processing data request',
    estimatedTimeRemaining: 120,
    lastUpdated: new Date(),
  };

  const mockQueryResult = {
    queryId: 'test-query-id',
    researcherId: 'HMS-12345',
    studyTitle: 'Test Study',
    submittedAt: new Date(),
    status: 'processing' as const,
    datasetSummary: {
      totalRecords: 1500,
      dataTypes: ['demographics', 'vital_signs'],
      dateRange: {
        startDate: '2023-01-01',
        endDate: '2023-12-31',
      },
      anonymizationMethods: ['k_anonymity', 'suppression'],
      privacyMetrics: {
        kAnonymity: 5,
        suppressionRate: 0.02,
        generalizationLevel: 'medium',
      },
    },
    processingLog: [
      {
        timestamp: new Date(),
        agent: 'Research Query Agent',
        action: 'Query Submitted',
        details: 'Research query received and queued for processing',
      },
      {
        timestamp: new Date(),
        agent: 'Privacy Agent',
        action: 'Processing Step',
        details: 'Applying privacy and anonymization rules',
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetQueryStatus.mockReturnValue(mockQueryStatus);
    mockGetQueryResult.mockReturnValue(mockQueryResult);
  });

  it('renders loading state when no status is available', () => {
    mockGetQueryStatus.mockReturnValue(null);
    mockGetQueryResult.mockReturnValue(null);

    render(<QueryStatusTracker queryId="test-query-id" />);
    
    expect(screen.getByText('Loading query status...')).toBeInTheDocument();
    expect(screen.getByTestId('refresh-icon')).toBeInTheDocument();
  });

  it('displays query status information', () => {
    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    expect(screen.getByText('Test Study')).toBeInTheDocument();
    expect(screen.getByText('Query ID: test-query-id')).toBeInTheDocument();
    expect(screen.getByText('PROCESSING')).toBeInTheDocument();
    expect(screen.getByText('Processing data request')).toBeInTheDocument();
  });

  it('shows progress bar with correct value', () => {
    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    const progressBar = screen.getByTestId('progress');
    expect(progressBar).toHaveAttribute('data-value', '60');
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('displays estimated time remaining', () => {
    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    expect(screen.getByText('Estimated time remaining: 2m 0s')).toBeInTheDocument();
  });

  it('shows error message when query fails', () => {
    const failedStatus = {
      ...mockQueryStatus,
      status: 'failed' as const,
      errorMessage: 'Query processing failed due to validation errors',
    };
    mockGetQueryStatus.mockReturnValue(failedStatus);

    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    expect(screen.getByTestId('alert')).toBeInTheDocument();
    expect(screen.getByText('Query processing failed due to validation errors')).toBeInTheDocument();
  });

  it('displays dataset summary for completed queries', () => {
    const completedStatus = { ...mockQueryStatus, status: 'completed' as const, progress: 100 };
    const completedResult = { 
      ...mockQueryResult, 
      status: 'completed' as const,
      completedAt: new Date(),
      downloadUrl: 'https://api.healthsync.com/downloads/test-query-id',
      expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    };
    
    mockGetQueryStatus.mockReturnValue(completedStatus);
    mockGetQueryResult.mockReturnValue(completedResult);

    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    expect(screen.getByText('Dataset Summary')).toBeInTheDocument();
    expect(screen.getByText('1,500')).toBeInTheDocument(); // Total records
    expect(screen.getByText('2')).toBeInTheDocument(); // Data types count
    expect(screen.getByText('k≥5')).toBeInTheDocument(); // K-anonymity
    expect(screen.getByText('2.0%')).toBeInTheDocument(); // Suppression rate
  });

  it('shows view results button for completed queries', () => {
    const completedStatus = { ...mockQueryStatus, status: 'completed' as const, progress: 100 };
    const completedResult = { 
      ...mockQueryResult, 
      status: 'completed' as const,
      completedAt: new Date(),
    };
    
    mockGetQueryStatus.mockReturnValue(completedStatus);
    mockGetQueryResult.mockReturnValue(completedResult);

    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    const viewResultsButton = screen.getByText('View Results');
    expect(viewResultsButton).toBeInTheDocument();
    
    fireEvent.click(viewResultsButton);
    expect(mockOnViewResults).toHaveBeenCalledWith('test-query-id');
  });

  it('shows download button when download URL is available', () => {
    const completedStatus = { ...mockQueryStatus, status: 'completed' as const, progress: 100 };
    const completedResult = { 
      ...mockQueryResult, 
      status: 'completed' as const,
      downloadUrl: 'https://api.healthsync.com/downloads/test-query-id',
    };
    
    mockGetQueryStatus.mockReturnValue(completedStatus);
    mockGetQueryResult.mockReturnValue(completedResult);

    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    expect(screen.getByText('Download Dataset')).toBeInTheDocument();
  });

  it('displays processing log entries', () => {
    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    expect(screen.getByText('Processing Log')).toBeInTheDocument();
    expect(screen.getByText('Query Submitted')).toBeInTheDocument();
    expect(screen.getByText('Research query received and queued for processing')).toBeInTheDocument();
    expect(screen.getByText('Research Query Agent')).toBeInTheDocument();
  });

  it('handles refresh button click', async () => {
    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    const refreshButton = screen.getByTestId('button');
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(mockGetQueryStatus).toHaveBeenCalledWith('test-query-id');
      expect(mockGetQueryResult).toHaveBeenCalledWith('test-query-id');
    });
  });

  it('shows correct status icons for different states', () => {
    // Test submitted status
    const submittedStatus = { ...mockQueryStatus, status: 'submitted' as const };
    const submittedResult = { ...mockQueryResult, status: 'submitted' as const };
    mockGetQueryStatus.mockReturnValue(submittedStatus);
    mockGetQueryResult.mockReturnValue(submittedResult);
    
    const { rerender } = render(<QueryStatusTracker queryId="test-query-id" />);
    expect(screen.getByTestId('clock-icon')).toBeInTheDocument();
    
    // Test completed status
    const completedStatus = { ...mockQueryStatus, status: 'completed' as const };
    const completedResult = { ...mockQueryResult, status: 'completed' as const };
    mockGetQueryStatus.mockReturnValue(completedStatus);
    mockGetQueryResult.mockReturnValue(completedResult);
    
    rerender(<QueryStatusTracker queryId="test-query-id" />);
    expect(screen.getByTestId('check-circle-icon')).toBeInTheDocument();
    
    // Test failed status
    const failedStatus = { ...mockQueryStatus, status: 'failed' as const };
    const failedResult = { ...mockQueryResult, status: 'failed' as const };
    mockGetQueryStatus.mockReturnValue(failedStatus);
    mockGetQueryResult.mockReturnValue(failedResult);
    
    rerender(<QueryStatusTracker queryId="test-query-id" />);
    expect(screen.getByTestId('x-circle-icon')).toBeInTheDocument();
  });

  it('displays researcher and submission information', () => {
    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    expect(screen.getByText('HMS-12345')).toBeInTheDocument();
    expect(screen.getByText('2 hours ago')).toBeInTheDocument();
  });

  it('shows expiration warning for completed datasets', () => {
    const completedStatus = { ...mockQueryStatus, status: 'completed' as const };
    const completedResult = { 
      ...mockQueryResult, 
      status: 'completed' as const,
      expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    };
    
    mockGetQueryStatus.mockReturnValue(completedStatus);
    mockGetQueryResult.mockReturnValue(completedResult);

    render(<QueryStatusTracker queryId="test-query-id" onViewResults={mockOnViewResults} />);
    
    expect(screen.getByText(/Dataset expires on/)).toBeInTheDocument();
  });

  it('formats time remaining correctly', () => {
    // Test seconds only
    const statusWithSeconds = { ...mockQueryStatus, estimatedTimeRemaining: 45 };
    const resultWithSeconds = { ...mockQueryResult };
    mockGetQueryStatus.mockReturnValue(statusWithSeconds);
    mockGetQueryResult.mockReturnValue(resultWithSeconds);
    
    const { rerender } = render(<QueryStatusTracker queryId="test-query-id" />);
    expect(screen.getByText('Estimated time remaining: 45s')).toBeInTheDocument();
    
    // Test minutes and seconds
    const statusWithMinutes = { ...mockQueryStatus, estimatedTimeRemaining: 125 };
    const resultWithMinutes = { ...mockQueryResult };
    mockGetQueryStatus.mockReturnValue(statusWithMinutes);
    mockGetQueryResult.mockReturnValue(resultWithMinutes);
    
    rerender(<QueryStatusTracker queryId="test-query-id" />);
    expect(screen.getByText('Estimated time remaining: 2m 5s')).toBeInTheDocument();
  });
});