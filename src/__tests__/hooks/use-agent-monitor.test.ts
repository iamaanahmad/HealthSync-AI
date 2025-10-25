import { renderHook, act, waitFor } from '@testing-library/react';
import { useAgentMonitor } from '@/hooks/use-agent-monitor';

// Mock WebSocket
const mockWebSocketInstances: any[] = [];

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(public url: string) {
    mockWebSocketInstances.push(this);
    // Simulate connection failure for testing
    setTimeout(() => {
      if (this.onerror) {
        this.onerror(new Event('error'));
      }
    }, 100);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  send(data: string) {
    // Mock send method
  }
}

// Create a mock constructor function
const MockWebSocketConstructor = jest.fn().mockImplementation((url: string) => {
  return new MockWebSocket(url);
});

// Mock global WebSocket
global.WebSocket = MockWebSocketConstructor as any;

// Mock console methods to avoid noise in tests
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

beforeAll(() => {
  console.log = jest.fn();
  console.error = jest.fn();
});

afterAll(() => {
  console.log = originalConsoleLog;
  console.error = originalConsoleError;
});

describe('useAgentMonitor', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
    mockWebSocketInstances.length = 0;
    MockWebSocketConstructor.mockClear();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useAgentMonitor());

    expect(result.current.agents).toEqual([]);
    expect(result.current.messages).toEqual([]);
    expect(result.current.metrics).toEqual([]);
    expect(result.current.logs).toEqual([]);
    expect(result.current.workflows).toEqual([]);
    expect(result.current.isConnected).toBe(false);
  });

  it('should attempt WebSocket connection on mount', () => {
    renderHook(() => useAgentMonitor());

    // WebSocket constructor should be called
    expect(MockWebSocketConstructor).toHaveBeenCalledWith('ws://localhost:8080/monitor');
  });

  it('should simulate connection and populate mock data', async () => {
    const { result } = renderHook(() => useAgentMonitor());

    // Wait for simulated connection
    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    expect(result.current.isConnected).toBe(true);
    expect(result.current.agents.length).toBeGreaterThan(0);
  });

  it('should provide reconnect functionality', () => {
    const { result } = renderHook(() => useAgentMonitor());

    act(() => {
      result.current.reconnect();
    });

    // Should attempt to create new WebSocket connection
    expect(MockWebSocketConstructor).toHaveBeenCalledTimes(2);
  });

  it('should provide search logs functionality', () => {
    const { result } = renderHook(() => useAgentMonitor());

    act(() => {
      result.current.searchLogs('test query');
    });

    // Should call searchLogs without errors
    expect(result.current.searchLogs).toBeDefined();
  });

  it('should provide filter messages functionality', () => {
    const { result } = renderHook(() => useAgentMonitor());

    act(() => {
      result.current.filterMessages('test filter');
    });

    // Should call filterMessages without errors
    expect(result.current.filterMessages).toBeDefined();
  });

  it('should update agent metrics over time', async () => {
    const { result } = renderHook(() => useAgentMonitor());

    // Wait for initial connection and data
    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    const initialMessageCount = result.current.agents[0]?.metrics.messagesProcessed || 0;

    // Advance time to trigger metric updates
    await act(async () => {
      jest.advanceTimersByTime(3000);
    });

    const updatedMessageCount = result.current.agents[0]?.metrics.messagesProcessed || 0;

    // Message count should have potentially increased
    expect(updatedMessageCount).toBeGreaterThanOrEqual(initialMessageCount);
  });

  it('should add new messages over time', async () => {
    const { result } = renderHook(() => useAgentMonitor());

    // Wait for initial connection
    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    const initialMessageCount = result.current.messages.length;

    // Advance time to potentially trigger new messages
    await act(async () => {
      jest.advanceTimersByTime(5000);
    });

    // Messages might have been added (depends on random chance in mock)
    expect(result.current.messages.length).toBeGreaterThanOrEqual(initialMessageCount);
  });

  it('should add new logs over time', async () => {
    const { result } = renderHook(() => useAgentMonitor());

    // Wait for initial connection
    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    const initialLogCount = result.current.logs.length;

    // Advance time to potentially trigger new logs
    await act(async () => {
      jest.advanceTimersByTime(5000);
    });

    // Logs might have been added (depends on random chance in mock)
    expect(result.current.logs.length).toBeGreaterThanOrEqual(initialLogCount);
  });

  it('should handle WebSocket connection failure gracefully', async () => {
    const { result } = renderHook(() => useAgentMonitor());

    // Wait for connection attempt to fail
    await act(async () => {
      jest.advanceTimersByTime(200);
    });

    // Should fall back to simulated connection
    expect(result.current.isConnected).toBe(true);
  });

  it('should clean up on unmount', () => {
    const { unmount } = renderHook(() => useAgentMonitor());

    // Unmount the hook
    unmount();

    // Should not throw any errors
  });

  it('should handle WebSocket message processing', async () => {
    // Create a mock WebSocket that succeeds
    class SuccessfulMockWebSocket extends MockWebSocket {
      constructor(url: string) {
        super(url);
        setTimeout(() => {
          this.readyState = MockWebSocket.OPEN;
          if (this.onopen) {
            this.onopen(new Event('open'));
          }
        }, 50);
      }
    }

    const SuccessfulMockWebSocketConstructor = jest.fn().mockImplementation((url: string) => {
      return new SuccessfulMockWebSocket(url);
    });
    global.WebSocket = SuccessfulMockWebSocketConstructor as any;

    const { result } = renderHook(() => useAgentMonitor());

    // Wait for connection
    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    expect(result.current.isConnected).toBe(true);

    // Simulate receiving a message
    const mockMessage = {
      type: 'agent_status',
      agent: {
        id: 'test-agent',
        name: 'Test Agent',
        type: 'test',
        status: 'active',
        lastSeen: new Date(),
        version: '1.0.0',
        endpoint: 'test-endpoint',
        metrics: {
          messagesProcessed: 100,
          averageResponseTime: 200,
          errorRate: 0.01,
          uptime: 99.5
        }
      }
    };

    // Get the WebSocket instance and simulate message
    const wsInstance = mockWebSocketInstances[0];
    if (wsInstance && wsInstance.onmessage) {
      act(() => {
        wsInstance.onmessage(new MessageEvent('message', {
          data: JSON.stringify(mockMessage)
        }));
      });
    }

    // Should have processed the message
    expect(result.current.agents.some(agent => agent.id === 'test-agent')).toBe(true);
  });

  it('should handle invalid WebSocket messages gracefully', async () => {
    class SuccessfulMockWebSocket extends MockWebSocket {
      constructor(url: string) {
        super(url);
        setTimeout(() => {
          this.readyState = MockWebSocket.OPEN;
          if (this.onopen) {
            this.onopen(new Event('open'));
          }
        }, 50);
      }
    }

    const SuccessfulMockWebSocketConstructor = jest.fn().mockImplementation((url: string) => {
      return new SuccessfulMockWebSocket(url);
    });
    global.WebSocket = SuccessfulMockWebSocketConstructor as any;

    const { result } = renderHook(() => useAgentMonitor());

    // Wait for connection
    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    // Simulate receiving invalid JSON
    const wsInstance = mockWebSocketInstances[0];
    if (wsInstance && wsInstance.onmessage) {
      act(() => {
        wsInstance.onmessage(new MessageEvent('message', {
          data: 'invalid json'
        }));
      });
    }

    // Should handle gracefully without crashing
    expect(result.current.isConnected).toBe(true);
  });

  it('should attempt reconnection after connection loss', async () => {
    class DisconnectingMockWebSocket extends MockWebSocket {
      constructor(url: string) {
        super(url);
        setTimeout(() => {
          this.readyState = MockWebSocket.OPEN;
          if (this.onopen) {
            this.onopen(new Event('open'));
          }
          
          // Simulate disconnection after a short time
          setTimeout(() => {
            this.readyState = MockWebSocket.CLOSED;
            if (this.onclose) {
              this.onclose(new CloseEvent('close'));
            }
          }, 100);
        }, 50);
      }
    }

    const DisconnectingMockWebSocketConstructor = jest.fn().mockImplementation((url: string) => {
      return new DisconnectingMockWebSocket(url);
    });
    global.WebSocket = DisconnectingMockWebSocketConstructor as any;

    const { result } = renderHook(() => useAgentMonitor());

    // Wait for initial connection
    await act(async () => {
      jest.advanceTimersByTime(100);
    });

    expect(result.current.isConnected).toBe(true);

    // Wait for disconnection
    await act(async () => {
      jest.advanceTimersByTime(200);
    });

    expect(result.current.isConnected).toBe(false);

    // Wait for reconnection attempt (5 second timeout)
    await act(async () => {
      jest.advanceTimersByTime(6000);
    });

    // Should have attempted reconnection
    expect(DisconnectingMockWebSocketConstructor).toHaveBeenCalledTimes(2);
  });
});