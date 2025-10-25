import { render, screen, fireEvent } from '@testing-library/react';
import MonitorPage from '@/app/(app)/monitor/page';
import { useAgentMonitor } from '@/hooks/use-agent-monitor';

// Mock the hook
jest.mock('@/hooks/use-agent-monitor');
const mockUseAgentMonitor = useAgentMonitor as jest.MockedFunction<typeof useAgentMonitor>;

// Mock recharts
jest.mock('recharts', () => ({
  LineChart: jest.fn(() => null),
  Line: jest.fn(() => null),
  XAxis: jest.fn(() => null),
  YAxis: jest.fn(() => null),
  CartesianGrid: jest.fn(() => null),
  Tooltip: jest.fn(() => null),
  Legend: jest.fn(() => null),
  ResponsiveContainer: jest.fn(() => null),
  BarChart: jest.fn(() => null),
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
  }
];

describe('MonitorPage', () => {
  beforeEach(() => {
    mockUseAgentMonitor.mockReturnValue({
      agents: mockAgents,
      messages: [],
      metrics: [],
      logs: [],
      workflows: [],
      isConnected: true,
      reconnect: jest.fn(),
      searchLogs: jest.fn(),
      filterMessages: jest.fn()
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render the monitor page with basic elements', () => {
    render(<MonitorPage />);

    expect(screen.getByText('Agent Activity Monitor')).toBeInTheDocument();
    expect(screen.getByText('Real-time monitoring of agent status, communication, and workflows')).toBeInTheDocument();
  });

  it('should display connection status', () => {
    render(<MonitorPage />);

    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('should show overview cards with metrics', () => {
    render(<MonitorPage />);

    expect(screen.getByText('Active Agents')).toBeInTheDocument();
    expect(screen.getByText('Messages Today')).toBeInTheDocument();
    expect(screen.getByText('Active Workflows')).toBeInTheDocument();
    expect(screen.getByText('System Health')).toBeInTheDocument();
  });

  it('should display tabs for different views', () => {
    render(<MonitorPage />);

    expect(screen.getByText('Agent Status')).toBeInTheDocument();
    expect(screen.getByText('Communication')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('Logs')).toBeInTheDocument();
    expect(screen.getByText('Workflows')).toBeInTheDocument();
  });

  it('should show reconnect button when disconnected', () => {
    mockUseAgentMonitor.mockReturnValue({
      agents: mockAgents,
      messages: [],
      metrics: [],
      logs: [],
      workflows: [],
      isConnected: false,
      reconnect: jest.fn(),
      searchLogs: jest.fn(),
      filterMessages: jest.fn()
    });

    render(<MonitorPage />);

    expect(screen.getByText('Disconnected')).toBeInTheDocument();
    expect(screen.getByText('Reconnect')).toBeInTheDocument();
  });

  it('should switch between tabs', () => {
    render(<MonitorPage />);

    // Click on Communication tab
    const communicationTab = screen.getByText('Communication');
    fireEvent.click(communicationTab);

    // Should show communication content
    expect(screen.getByText('Agent Communication Flow')).toBeInTheDocument();
  });
});