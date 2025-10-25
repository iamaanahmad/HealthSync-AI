import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { useAgentMonitor } from '@/hooks/use-agent-monitor';
import MonitorPage from '@/app/(app)/monitor/page';

// Mock the hook
jest.mock('@/hooks/use-agent-monitor');
const mockUseAgentMonitor = useAgentMonitor as jest.MockedFunction<typeof useAgentMonitor>;

// Mock recharts to avoid canvas issues in tests
jest.mock('recharts', () => ({
  LineChart: jest.fn(({ children }) => children),
  Line: jest.fn(() => null),
  XAxis: jest.fn(() => null),
  YAxis: jest.fn(() => null),
  CartesianGrid: jest.fn(() => null),
  Tooltip: jest.fn(() => null),
  Legend: jest.fn(() => null),
  ResponsiveContainer: jest.fn(({ children }) => children),
  BarChart: jest.fn(({ children }) => children),
  Bar: jest.fn(() => null),
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn(() => '2 minutes ago'),
  format: jest.fn(() => '10:30:45'),
  subHours: jest.fn(() => new Date()),
  isAfter: jest.fn(() => true),
  differenceInMilliseconds: jest.fn(() => 120000),
}));

const mockAgents = [
  {
    id: 'patient-consent',
    name: 'Patient Consent Agent',
    type: 'consent',
    status: 'active' as const,
    lastSeen: new Date(),
    version: '1.0.0',
    endpoint: 'agent1qw5jxw4k8h7z2x9v3n6m8l4p2r7t5y9u3i6o8e1w4r7t2y5u8i0p3s6d9f2g5h8j1k4n7q0w3e6r9t2y5u8',
    metrics: {
      messagesProcessed: 1247,
      averageResponseTime: 145,
      errorRate: 0.02,
      uptime: 99.8
    }
  },
  {
    id: 'data-custodian',
    name: 'Data Custodian Agent',
    type: 'data',
    status: 'active' as const,
    lastSeen: new Date(),
    version: '1.0.0',
    endpoint: 'agent1qx8k2m5n9p1r4t7w0z3c6v9b2n5m8k1j4h7g0f3d6s9a2p5o8i1u4y7r0e3w6q9t2y5u8i0p3s6d9f2g5h8j1k4',
    metrics: {
      messagesProcessed: 892,
      averageResponseTime: 234,
      errorRate: 0.01,
      uptime: 99.9
    }
  }
];

const mockMessages = [
  {
    id: 'msg-1',
    timestamp: new Date(),
    sender: 'patient-consent',
    recipient: 'data-custodian',
    type: 'consent_request',
    status: 'processed' as const,
    payload: { consentType: 'research_data' },
    processingTime: 150
  }
];

const mockLogs = [
  {
    id: 'log-1',
    timestamp: new Date(),
    level: 'info' as const,
    agentId: 'patient-consent',
    message: 'Consent request processed successfully',
    context: { requestId: 'req-123' }
  }
];

const mockWorkflows = [
  {
    id: 'wf-1',
    name: 'Patient Consent Update',
    status: 'completed' as const,
    startTime: new Date(Date.now() - 5 * 60 * 1000),
    endTime: new Date(Date.now() - 2 * 60 * 1000),
    currentStep: 2,
    steps: [
      {
        id: 'step-1',
        name: 'Receive Consent Request',
        agentId: 'patient-consent',
        status: 'completed' as const,
        startTime: new Date(Date.now() - 5 * 60 * 1000),
        endTime: new Date(Date.now() - 4 * 60 * 1000),
        result: { consent_type: 'research_data' }
      }
    ]
  }
];

describe('Agent Monitor Integration', () => {
  beforeEach(() => {
    mockUseAgentMonitor.mockReturnValue({
      agents: mockAgents,
      messages: mockMessages,
      metrics: [],
      logs: mockLogs,
      workflows: mockWorkflows,
      isConnected: true,
      reconnect: jest.fn(),
      searchLogs: jest.fn(),
      filterMessages: jest.fn()
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Real-time Agent Status Monitoring', () => {
    it('should display agent status grid with real-time updates', async () => {
      render(<MonitorPage />);

      // Check if agent status cards are displayed
      expect(screen.getByText('Patient Consent Agent')).toBeInTheDocument();
      expect(screen.getByText('Data Custodian Agent')).toBeInTheDocument();

      // Check if status indicators are shown
      expect(screen.getAllByText('active')).toHaveLength(2);

      // Check if metrics are displayed
      expect(screen.getByText('1,247')).toBeInTheDocument(); // messages processed
      expect(screen.getByText('892')).toBeInTheDocument();
    });

    it('should show connection status and allow reconnection', async () => {
      const mockReconnect = jest.fn();
      mockUseAgentMonitor.mockReturnValue({
        agents: mockAgents,
        messages: mockMessages,
        metrics: [],
        logs: mockLogs,
        workflows: mockWorkflows,
        isConnected: false,
        reconnect: mockReconnect,
        searchLogs: jest.fn(),
        filterMessages: jest.fn()
      });

      render(<MonitorPage />);

      // Check disconnected status
      expect(screen.getByText('Disconnected')).toBeInTheDocument();

      // Click reconnect button
      const reconnectButton = screen.getByText('Reconnect');
      fireEvent.click(reconnectButton);

      expect(mockReconnect).toHaveBeenCalled();
    });

    it('should allow agent selection and filtering', async () => {
      render(<MonitorPage />);

      // Click on an agent card
      const agentCard = screen.getByText('Patient Consent Agent').closest('div');
      if (agentCard) {
        fireEvent.click(agentCard);
      }

      // Should show agent-specific information
      await waitFor(() => {
        expect(screen.getByText('View Logs')).toBeInTheDocument();
        expect(screen.getByText('Restart')).toBeInTheDocument();
      });
    });
  });

  describe('Message Flow Visualization', () => {
    it('should display message flow diagram', async () => {
      render(<MonitorPage />);

      // Switch to communication tab
      const communicationTab = screen.getByText('Communication');
      fireEvent.click(communicationTab);

      // Check if message flow components are rendered
      expect(screen.getByText('Agent Communication Flow')).toBeInTheDocument();
      expect(screen.getByText('Recent Messages')).toBeInTheDocument();
    });

    it('should show message details when clicked', async () => {
      render(<MonitorPage />);

      // Switch to communication tab
      const communicationTab = screen.getByText('Communication');
      fireEvent.click(communicationTab);

      // Find and click on a message
      const messageElement = screen.getByText('consent_request');
      fireEvent.click(messageElement.closest('div')!);

      // Should show message payload
      await waitFor(() => {
        expect(screen.getByText('Payload:')).toBeInTheDocument();
      });
    });

    it('should filter messages by search term', async () => {
      const mockFilterMessages = jest.fn();
      mockUseAgentMonitor.mockReturnValue({
        agents: mockAgents,
        messages: mockMessages,
        metrics: [],
        logs: mockLogs,
        workflows: mockWorkflows,
        isConnected: true,
        reconnect: jest.fn(),
        searchLogs: jest.fn(),
        filterMessages: mockFilterMessages
      });

      render(<MonitorPage />);

      // Switch to communication tab
      const communicationTab = screen.getByText('Communication');
      fireEvent.click(communicationTab);

      // Enter search term
      const searchInput = screen.getByPlaceholderText('Filter messages...');
      fireEvent.change(searchInput, { target: { value: 'consent' } });

      // Click filter button
      const filterButton = screen.getByText('Filter');
      fireEvent.click(filterButton);

      expect(mockFilterMessages).toHaveBeenCalledWith('consent');
    });
  });

  describe('Performance Metrics Display', () => {
    it('should display performance metrics with charts', async () => {
      render(<MonitorPage />);

      // Switch to performance tab
      const performanceTab = screen.getByText('Performance');
      fireEvent.click(performanceTab);

      // Check if performance components are rendered
      expect(screen.getByText('Response Time Over Time')).toBeInTheDocument();
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should allow metric type and time range selection', async () => {
      render(<MonitorPage />);

      // Switch to performance tab
      const performanceTab = screen.getByText('Performance');
      fireEvent.click(performanceTab);

      // Check if select components are present
      expect(screen.getByText('Select agent')).toBeInTheDocument();
      expect(screen.getByText('Select metric')).toBeInTheDocument();
    });

    it('should show performance alerts for threshold violations', async () => {
      render(<MonitorPage />);

      // Switch to performance tab
      const performanceTab = screen.getByText('Performance');
      fireEvent.click(performanceTab);

      // Check if alerts section is present
      expect(screen.getByText('Performance Alerts')).toBeInTheDocument();
    });
  });

  describe('Log Aggregation and Search', () => {
    it('should display log entries with filtering', async () => {
      render(<MonitorPage />);

      // Switch to logs tab
      const logsTab = screen.getByText('Logs');
      fireEvent.click(logsTab);

      // Check if log viewer is rendered
      expect(screen.getByText('Log Viewer')).toBeInTheDocument();
      expect(screen.getByText('Consent request processed successfully')).toBeInTheDocument();
    });

    it('should search logs when search function is called', async () => {
      const mockSearchLogs = jest.fn();
      mockUseAgentMonitor.mockReturnValue({
        agents: mockAgents,
        messages: mockMessages,
        metrics: [],
        logs: mockLogs,
        workflows: mockWorkflows,
        isConnected: true,
        reconnect: jest.fn(),
        searchLogs: mockSearchLogs,
        filterMessages: jest.fn()
      });

      render(<MonitorPage />);

      // Switch to logs tab
      const logsTab = screen.getByText('Logs');
      fireEvent.click(logsTab);

      // Enter search term
      const searchInput = screen.getByPlaceholderText('Search logs...');
      fireEvent.change(searchInput, { target: { value: 'consent' } });

      // Press Enter or click search
      fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });

      expect(mockSearchLogs).toHaveBeenCalledWith('consent');
    });

    it('should filter logs by level', async () => {
      render(<MonitorPage />);

      // Switch to logs tab
      const logsTab = screen.getByText('Logs');
      fireEvent.click(logsTab);

      // Check if log level filters are available
      expect(screen.getByText('All Levels')).toBeInTheDocument();
    });

    it('should export logs when export button is clicked', async () => {
      // Mock URL.createObjectURL and related functions
      global.URL.createObjectURL = jest.fn(() => 'mock-url');
      global.URL.revokeObjectURL = jest.fn();
      
      const mockAppendChild = jest.fn();
      const mockRemoveChild = jest.fn();
      const mockClick = jest.fn();
      
      Object.defineProperty(document, 'createElement', {
        value: jest.fn(() => ({
          href: '',
          download: '',
          click: mockClick
        }))
      });
      
      Object.defineProperty(document.body, 'appendChild', {
        value: mockAppendChild
      });
      
      Object.defineProperty(document.body, 'removeChild', {
        value: mockRemoveChild
      });

      render(<MonitorPage />);

      // Switch to logs tab
      const logsTab = screen.getByText('Logs');
      fireEvent.click(logsTab);

      // Click export button
      const exportButton = screen.getByText('Export');
      fireEvent.click(exportButton);

      expect(mockClick).toHaveBeenCalled();
    });
  });

  describe('Workflow Progress Tracking', () => {
    it('should display workflow tracker with step-by-step visualization', async () => {
      render(<MonitorPage />);

      // Switch to workflows tab
      const workflowsTab = screen.getByText('Workflows');
      fireEvent.click(workflowsTab);

      // Check if workflow components are rendered
      expect(screen.getByText('Active Workflows')).toBeInTheDocument();
      expect(screen.getByText('Patient Consent Update')).toBeInTheDocument();
    });

    it('should show workflow statistics', async () => {
      render(<MonitorPage />);

      // Switch to workflows tab
      const workflowsTab = screen.getByText('Workflows');
      fireEvent.click(workflowsTab);

      // Check if statistics are displayed
      expect(screen.getByText('Total Workflows')).toBeInTheDocument();
      expect(screen.getByText('Running')).toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });

    it('should show workflow details when selected', async () => {
      render(<MonitorPage />);

      // Switch to workflows tab
      const workflowsTab = screen.getByText('Workflows');
      fireEvent.click(workflowsTab);

      // Click on a workflow
      const workflowCard = screen.getByText('Patient Consent Update').closest('div');
      if (workflowCard) {
        fireEvent.click(workflowCard);
      }

      // Should show workflow details
      await waitFor(() => {
        expect(screen.getByText('Workflow Details')).toBeInTheDocument();
        expect(screen.getByText('Receive Consent Request')).toBeInTheDocument();
      });
    });
  });

  describe('WebSocket Connection Management', () => {
    it('should handle connection state changes', async () => {
      const { rerender } = render(<MonitorPage />);

      // Initially connected
      expect(screen.getByText('Connected')).toBeInTheDocument();

      // Simulate disconnection
      mockUseAgentMonitor.mockReturnValue({
        agents: mockAgents,
        messages: mockMessages,
        metrics: [],
        logs: mockLogs,
        workflows: mockWorkflows,
        isConnected: false,
        reconnect: jest.fn(),
        searchLogs: jest.fn(),
        filterMessages: jest.fn()
      });

      rerender(<MonitorPage />);

      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.getByText('Reconnect')).toBeInTheDocument();
    });
  });

  describe('Real-time Updates', () => {
    it('should update agent metrics in real-time', async () => {
      const { rerender } = render(<MonitorPage />);

      // Initial state
      expect(screen.getByText('1,247')).toBeInTheDocument();

      // Update metrics
      const updatedAgents = [
        {
          ...mockAgents[0],
          metrics: {
            ...mockAgents[0].metrics,
            messagesProcessed: 1250
          }
        },
        mockAgents[1]
      ];

      mockUseAgentMonitor.mockReturnValue({
        agents: updatedAgents,
        messages: mockMessages,
        metrics: [],
        logs: mockLogs,
        workflows: mockWorkflows,
        isConnected: true,
        reconnect: jest.fn(),
        searchLogs: jest.fn(),
        filterMessages: jest.fn()
      });

      rerender(<MonitorPage />);

      expect(screen.getByText('1,250')).toBeInTheDocument();
    });
  });
});