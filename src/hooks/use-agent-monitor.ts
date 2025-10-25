import { useState, useEffect, useCallback, useRef } from 'react';

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'error' | 'starting';
  lastSeen: Date;
  version: string;
  endpoint: string;
  metrics: {
    messagesProcessed: number;
    averageResponseTime: number;
    errorRate: number;
    uptime: number;
  };
}

export interface AgentMessage {
  id: string;
  timestamp: Date;
  sender: string;
  recipient: string;
  type: string;
  status: 'sent' | 'delivered' | 'processed' | 'failed';
  payload: any;
  processingTime?: number;
}

export interface PerformanceMetric {
  timestamp: Date;
  agentId: string;
  metric: string;
  value: number;
  unit: string;
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'info' | 'warn' | 'error' | 'debug';
  agentId: string;
  message: string;
  context?: any;
}

export interface Workflow {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'paused';
  startTime: Date;
  endTime?: Date;
  steps: WorkflowStep[];
  currentStep: number;
}

export interface WorkflowStep {
  id: string;
  name: string;
  agentId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
  result?: any;
}

export function useAgentMonitor() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      // In a real implementation, this would connect to the actual WebSocket server
      // For demo purposes, we'll simulate the connection
      const ws = new WebSocket('ws://localhost:8080/monitor');
      
      ws.onopen = () => {
        console.log('Connected to agent monitor WebSocket');
        setIsConnected(true);
        
        // Clear any existing reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('Disconnected from agent monitor WebSocket');
        setIsConnected(false);
        
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      setIsConnected(false);
      
      // Simulate connection for demo purposes
      simulateConnection();
    }
  }, []);

  const simulateConnection = useCallback(() => {
    setIsConnected(true);
    
    // Initialize with mock data
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
        status: 'active',
        lastSeen: new Date(),
        version: '1.0.0',
        endpoint: 'agent1qx8k2m5n9p1r4t7w0z3c6v9b2n5m8k1j4h7g0f3d6s9a2p5o8i1u4y7r0e3w6q9t2y5u8i0p3s6d9f2g5h8j1k4',
        metrics: {
          messagesProcessed: 892,
          averageResponseTime: 234,
          errorRate: 0.01,
          uptime: 99.9
        }
      },
      {
        id: 'research-query',
        name: 'Research Query Agent',
        type: 'query',
        status: 'active',
        lastSeen: new Date(),
        version: '1.0.0',
        endpoint: 'agent1qz7j3k6l9o2p5s8v1y4b7e0h3k6n9q2t5w8z1c4f7i0l3o6r9u2x5a8d1g4j7m0p3s6v9y2b5e8h1k4n7q0w3e6r9',
        metrics: {
          messagesProcessed: 456,
          averageResponseTime: 567,
          errorRate: 0.03,
          uptime: 98.5
        }
      },
      {
        id: 'privacy',
        name: 'Privacy Agent',
        type: 'privacy',
        status: 'active',
        lastSeen: new Date(),
        version: '1.0.0',
        endpoint: 'agent1qy6h2j5k8n1q4t7w0z3c6v9b2m5p8s1u4x7a0d3g6j9l2o5r8u1x4z7c0f3i6l9o2r5u8x1a4d7g0j3m6p9s2v5y8b1e4',
        metrics: {
          messagesProcessed: 678,
          averageResponseTime: 189,
          errorRate: 0.01,
          uptime: 99.7
        }
      },
      {
        id: 'metta-integration',
        name: 'MeTTa Integration Agent',
        type: 'knowledge',
        status: 'active',
        lastSeen: new Date(),
        version: '1.0.0',
        endpoint: 'agent1qx5g1h4j7m0p3s6v9y2b5e8k1n4q7t0w3z6c9f2i5l8o1r4u7x0a3d6g9j2m5p8s1v4y7b0e3h6k9n2q5t8w1z4c7f0i3l6',
        metrics: {
          messagesProcessed: 1123,
          averageResponseTime: 298,
          errorRate: 0.02,
          uptime: 99.4
        }
      }
    ];

    setAgents(mockAgents);
    
    // Simulate real-time updates
    const interval = setInterval(() => {
      // Update agent metrics
      setAgents(prev => prev.map(agent => ({
        ...agent,
        lastSeen: new Date(),
        metrics: {
          ...agent.metrics,
          messagesProcessed: agent.metrics.messagesProcessed + Math.floor(Math.random() * 5),
          averageResponseTime: agent.metrics.averageResponseTime + (Math.random() - 0.5) * 20
        }
      })));

      // Add new messages
      if (Math.random() > 0.7) {
        const senders = mockAgents.map(a => a.id);
        const sender = senders[Math.floor(Math.random() * senders.length)];
        const recipients = senders.filter(s => s !== sender);
        const recipient = recipients[Math.floor(Math.random() * recipients.length)];

        const newMessage: AgentMessage = {
          id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          sender,
          recipient,
          type: ['consent_request', 'data_query', 'privacy_check', 'metta_query'][Math.floor(Math.random() * 4)],
          status: 'sent',
          payload: { data: 'sample payload' },
          processingTime: Math.floor(Math.random() * 500) + 50
        };

        setMessages(prev => [newMessage, ...prev.slice(0, 99)]);
      }

      // Add new logs
      if (Math.random() > 0.8) {
        const agentIds = mockAgents.map(a => a.id);
        const agentId = agentIds[Math.floor(Math.random() * agentIds.length)];
        const levels: LogEntry['level'][] = ['info', 'warn', 'error', 'debug'];
        const level = levels[Math.floor(Math.random() * levels.length)];

        const newLog: LogEntry = {
          id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          level,
          agentId,
          message: `Sample log message from ${agentId}`,
          context: { operation: 'sample_operation' }
        };

        setLogs(prev => [newLog, ...prev.slice(0, 199)]);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'agent_status':
        setAgents(prev => {
          const index = prev.findIndex(a => a.id === data.agent.id);
          if (index >= 0) {
            const updated = [...prev];
            updated[index] = { ...updated[index], ...data.agent };
            return updated;
          }
          return [...prev, data.agent];
        });
        break;

      case 'agent_message':
        setMessages(prev => [data.message, ...prev.slice(0, 99)]);
        break;

      case 'performance_metric':
        setMetrics(prev => [data.metric, ...prev.slice(0, 999)]);
        break;

      case 'log_entry':
        setLogs(prev => [data.log, ...prev.slice(0, 199)]);
        break;

      case 'workflow_update':
        setWorkflows(prev => {
          const index = prev.findIndex(w => w.id === data.workflow.id);
          if (index >= 0) {
            const updated = [...prev];
            updated[index] = { ...updated[index], ...data.workflow };
            return updated;
          }
          return [...prev, data.workflow];
        });
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }, []);

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    connect();
  }, [connect]);

  const searchLogs = useCallback((query: string) => {
    // In a real implementation, this would send a search request to the server
    console.log('Searching logs for:', query);
  }, []);

  const filterMessages = useCallback((filter: string) => {
    // In a real implementation, this would filter messages on the server
    console.log('Filtering messages with:', filter);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return {
    agents,
    messages,
    metrics,
    logs,
    workflows,
    isConnected,
    reconnect,
    searchLogs,
    filterMessages
  };
}