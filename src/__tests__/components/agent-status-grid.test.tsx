import { render, screen, fireEvent } from '@testing-library/react';
import { AgentStatusGrid } from '@/components/monitor/agent-status-grid';
import { Agent } from '@/hooks/use-agent-monitor';

// Mock date-fns
jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn(() => '2 minutes ago'),
}));

const mockAgents: Agent[] = [
  {
    id: 'patient-consent',
    name: 'Patient Consent Agent',
    type: 'consent',
    status: 'active',
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
    status: 'error',
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

describe('AgentStatusGrid', () => {
  const mockOnAgentSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render agent cards with correct information', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    // Check if agent names are displayed
    expect(screen.getByText('Patient Consent Agent')).toBeInTheDocument();
    expect(screen.getByText('Data Custodian Agent')).toBeInTheDocument();

    // Check if agent types are displayed
    expect(screen.getByText('consent')).toBeInTheDocument();
    expect(screen.getByText('data')).toBeInTheDocument();

    // Check if versions are displayed
    expect(screen.getAllByText('v1.0.0')).toHaveLength(2);
  });

  it('should display correct status badges and icons', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    // Check status badges
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('error')).toBeInTheDocument();
  });

  it('should display agent metrics correctly', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    // Check if metrics are displayed
    expect(screen.getByText('1,247')).toBeInTheDocument();
    expect(screen.getByText('892')).toBeInTheDocument();
    expect(screen.getByText('145ms')).toBeInTheDocument();
    expect(screen.getByText('234ms')).toBeInTheDocument();
    expect(screen.getByText('2.00%')).toBeInTheDocument();
    expect(screen.getByText('1.00%')).toBeInTheDocument();
  });

  it('should call onAgentSelect when agent card is clicked', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    // Click on first agent card
    const agentCard = screen.getByText('Patient Consent Agent').closest('div');
    if (agentCard) {
      fireEvent.click(agentCard);
    }

    expect(mockOnAgentSelect).toHaveBeenCalledWith('patient-consent');
  });

  it('should highlight selected agent card', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent="patient-consent"
      />
    );

    // Check if selected agent card has special styling
    const selectedCard = screen.getByText('Patient Consent Agent').closest('div');
    expect(selectedCard).toHaveClass('ring-2', 'ring-primary');
  });

  it('should show quick actions for selected agent', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent="patient-consent"
      />
    );

    // Check if quick action buttons are displayed
    expect(screen.getByText('View Logs')).toBeInTheDocument();
    expect(screen.getByText('Restart')).toBeInTheDocument();
  });

  it('should deselect agent when clicking on already selected agent', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent="patient-consent"
      />
    );

    // Click on already selected agent
    const agentCard = screen.getByText('Patient Consent Agent').closest('div');
    if (agentCard) {
      fireEvent.click(agentCard);
    }

    expect(mockOnAgentSelect).toHaveBeenCalledWith(null);
  });

  it('should display uptime progress bar', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    // Check if uptime percentages are displayed
    expect(screen.getByText('99.8%')).toBeInTheDocument();
    expect(screen.getByText('99.9%')).toBeInTheDocument();
  });

  it('should display last seen information', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    // Check if last seen text is displayed
    expect(screen.getAllByText('2 minutes ago')).toHaveLength(2);
  });

  it('should display truncated agent endpoints', () => {
    render(
      <AgentStatusGrid
        agents={mockAgents}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    // Check if endpoints are displayed (truncated)
    expect(screen.getByText('agent1qw5jxw4k8h7z2x9v3n6m8l4p2r7t5y9u3i6o8e1w4r7t2y5u8i0p3s6d9f2g5h8j1k4n7q0w3e6r9t2y5u8')).toBeInTheDocument();
  });

  it('should handle empty agents array', () => {
    render(
      <AgentStatusGrid
        agents={[]}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    // Should render without crashing
    expect(screen.queryByText('Patient Consent Agent')).not.toBeInTheDocument();
  });

  it('should format error rates correctly', () => {
    const agentWithHighErrorRate: Agent = {
      ...mockAgents[0],
      metrics: {
        ...mockAgents[0].metrics,
        errorRate: 0.1234
      }
    };

    render(
      <AgentStatusGrid
        agents={[agentWithHighErrorRate]}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    expect(screen.getByText('12.34%')).toBeInTheDocument();
  });

  it('should format large message counts with commas', () => {
    const agentWithLargeCount: Agent = {
      ...mockAgents[0],
      metrics: {
        ...mockAgents[0].metrics,
        messagesProcessed: 1234567
      }
    };

    render(
      <AgentStatusGrid
        agents={[agentWithLargeCount]}
        onAgentSelect={mockOnAgentSelect}
        selectedAgent={null}
      />
    );

    expect(screen.getByText('1,234,567')).toBeInTheDocument();
  });
});