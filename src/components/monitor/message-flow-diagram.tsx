'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Agent, AgentMessage } from '@/hooks/use-agent-monitor';
import { ArrowRight, MessageSquare, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface MessageFlowDiagramProps {
  messages: AgentMessage[];
  agents: Agent[];
  selectedAgent: string | null;
}

interface MessageFlowNode {
  id: string;
  name: string;
  type: string;
  x: number;
  y: number;
  messageCount: number;
}

interface MessageFlowEdge {
  from: string;
  to: string;
  messages: AgentMessage[];
  weight: number;
}

export function MessageFlowDiagram({ messages, agents, selectedAgent }: MessageFlowDiagramProps) {
  const [selectedMessage, setSelectedMessage] = useState<AgentMessage | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Create nodes from agents
  const nodes: MessageFlowNode[] = agents.map((agent, index) => {
    const angle = (index / agents.length) * 2 * Math.PI;
    const radius = 120;
    const centerX = 200;
    const centerY = 150;
    
    return {
      id: agent.id,
      name: agent.name,
      type: agent.type,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      messageCount: messages.filter(m => m.sender === agent.id || m.recipient === agent.id).length
    };
  });

  // Create edges from messages
  const edgeMap = new Map<string, MessageFlowEdge>();
  
  messages.forEach(message => {
    const key = `${message.sender}-${message.recipient}`;
    if (!edgeMap.has(key)) {
      edgeMap.set(key, {
        from: message.sender,
        to: message.recipient,
        messages: [],
        weight: 0
      });
    }
    const edge = edgeMap.get(key)!;
    edge.messages.push(message);
    edge.weight = edge.messages.length;
  });

  const edges = Array.from(edgeMap.values());

  const getStatusIcon = (status: AgentMessage['status']) => {
    switch (status) {
      case 'sent':
        return <Clock className="h-3 w-3 text-yellow-500" />;
      case 'delivered':
        return <ArrowRight className="h-3 w-3 text-blue-500" />;
      case 'processed':
        return <CheckCircle className="h-3 w-3 text-green-500" />;
      case 'failed':
        return <XCircle className="h-3 w-3 text-red-500" />;
      default:
        return <AlertTriangle className="h-3 w-3 text-gray-500" />;
    }
  };

  const getStatusColor = (status: AgentMessage['status']) => {
    switch (status) {
      case 'sent':
        return 'outline';
      case 'delivered':
        return 'secondary';
      case 'processed':
        return 'default';
      case 'failed':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const getNodeColor = (nodeId: string) => {
    if (selectedAgent === nodeId) return '#3b82f6';
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return '#6b7280';
    
    switch (node.type) {
      case 'consent': return '#10b981';
      case 'data': return '#f59e0b';
      case 'query': return '#8b5cf6';
      case 'privacy': return '#ef4444';
      case 'knowledge': return '#06b6d4';
      default: return '#6b7280';
    }
  };

  const filteredMessages = selectedAgent 
    ? messages.filter(m => m.sender === selectedAgent || m.recipient === selectedAgent)
    : messages;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Flow Diagram */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Agent Communication Flow
          </CardTitle>
          <CardDescription>
            Real-time visualization of inter-agent message flow
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <svg
              ref={svgRef}
              width="400"
              height="300"
              viewBox="0 0 400 300"
              className="border rounded-lg bg-muted/20"
            >
              {/* Edges */}
              {edges.map((edge, index) => {
                const fromNode = nodes.find(n => n.id === edge.from);
                const toNode = nodes.find(n => n.id === edge.to);
                
                if (!fromNode || !toNode) return null;

                const strokeWidth = Math.min(edge.weight / 2 + 1, 5);
                const opacity = selectedAgent 
                  ? (edge.from === selectedAgent || edge.to === selectedAgent ? 1 : 0.3)
                  : 0.7;

                return (
                  <g key={`edge-${index}`}>
                    <line
                      x1={fromNode.x}
                      y1={fromNode.y}
                      x2={toNode.x}
                      y2={toNode.y}
                      stroke="#6b7280"
                      strokeWidth={strokeWidth}
                      opacity={opacity}
                      markerEnd="url(#arrowhead)"
                    />
                    {/* Message count label */}
                    <text
                      x={(fromNode.x + toNode.x) / 2}
                      y={(fromNode.y + toNode.y) / 2 - 5}
                      textAnchor="middle"
                      fontSize="10"
                      fill="#6b7280"
                      opacity={opacity}
                    >
                      {edge.weight}
                    </text>
                  </g>
                );
              })}

              {/* Arrow marker */}
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon
                    points="0 0, 10 3.5, 0 7"
                    fill="#6b7280"
                  />
                </marker>
              </defs>

              {/* Nodes */}
              {nodes.map((node) => (
                <g key={node.id}>
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r="20"
                    fill={getNodeColor(node.id)}
                    opacity={selectedAgent && selectedAgent !== node.id ? 0.5 : 1}
                    className="cursor-pointer hover:opacity-80 transition-opacity"
                  />
                  <text
                    x={node.x}
                    y={node.y + 30}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#374151"
                    className="pointer-events-none"
                  >
                    {node.name.split(' ')[0]}
                  </text>
                  {/* Message count badge */}
                  <circle
                    cx={node.x + 15}
                    cy={node.y - 15}
                    r="8"
                    fill="#ef4444"
                    opacity={node.messageCount > 0 ? 1 : 0}
                  />
                  <text
                    x={node.x + 15}
                    y={node.y - 11}
                    textAnchor="middle"
                    fontSize="8"
                    fill="white"
                    className="pointer-events-none"
                  >
                    {node.messageCount}
                  </text>
                </g>
              ))}
            </svg>
          </div>
        </CardContent>
      </Card>

      {/* Message List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Messages</CardTitle>
          <CardDescription>
            {selectedAgent 
              ? `Messages for ${agents.find(a => a.id === selectedAgent)?.name || selectedAgent}`
              : 'All inter-agent communications'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            <div className="space-y-2">
              {filteredMessages.slice(0, 50).map((message) => (
                <div
                  key={message.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors hover:bg-muted/50 ${
                    selectedMessage?.id === message.id ? 'bg-muted' : ''
                  }`}
                  onClick={() => setSelectedMessage(
                    selectedMessage?.id === message.id ? null : message
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(message.status)}
                      <Badge variant={getStatusColor(message.status) as any} className="text-xs">
                        {message.type}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(message.timestamp, { addSuffix: true })}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">
                      {agents.find(a => a.id === message.sender)?.name || message.sender}
                    </span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <span className="font-medium">
                      {agents.find(a => a.id === message.recipient)?.name || message.recipient}
                    </span>
                  </div>

                  {message.processingTime && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Processing time: {message.processingTime}ms
                    </div>
                  )}

                  {selectedMessage?.id === message.id && (
                    <div className="mt-3 pt-3 border-t">
                      <div className="text-xs text-muted-foreground mb-2">Payload:</div>
                      <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                        {JSON.stringify(message.payload, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}