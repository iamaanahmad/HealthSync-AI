'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Agent } from '@/hooks/use-agent-monitor';
import { Activity, AlertTriangle, CheckCircle, Clock, ExternalLink } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface AgentStatusGridProps {
  agents: Agent[];
  onAgentSelect: (agentId: string | null) => void;
  selectedAgent: string | null;
}

export function AgentStatusGrid({ agents, onAgentSelect, selectedAgent }: AgentStatusGridProps) {
  const getStatusIcon = (status: Agent['status']) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'inactive':
        return <Clock className="h-4 w-4 text-gray-500" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'starting':
        return <Activity className="h-4 w-4 text-yellow-500 animate-pulse" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'active':
        return 'default';
      case 'inactive':
        return 'secondary';
      case 'error':
        return 'destructive';
      case 'starting':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const formatUptime = (uptime: number) => {
    return `${uptime.toFixed(1)}%`;
  };

  const formatResponseTime = (time: number) => {
    return `${Math.round(time)}ms`;
  };

  const formatErrorRate = (rate: number) => {
    return `${(rate * 100).toFixed(2)}%`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {agents.map((agent) => (
        <Card 
          key={agent.id}
          className={`cursor-pointer transition-all hover:shadow-md ${
            selectedAgent === agent.id ? 'ring-2 ring-primary' : ''
          }`}
          onClick={() => onAgentSelect(selectedAgent === agent.id ? null : agent.id)}
        >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getStatusIcon(agent.status)}
                <CardTitle className="text-lg">{agent.name}</CardTitle>
              </div>
              <Badge variant={getStatusColor(agent.status) as any}>
                {agent.status}
              </Badge>
            </div>
            <CardDescription className="flex items-center gap-2">
              <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
                {agent.type}
              </span>
              <span>v{agent.version}</span>
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">Messages</div>
                <div className="font-semibold">{agent.metrics.messagesProcessed.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Response Time</div>
                <div className="font-semibold">{formatResponseTime(agent.metrics.averageResponseTime)}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Error Rate</div>
                <div className="font-semibold">{formatErrorRate(agent.metrics.errorRate)}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Uptime</div>
                <div className="font-semibold">{formatUptime(agent.metrics.uptime)}</div>
              </div>
            </div>

            {/* Uptime Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">System Health</span>
                <span className="font-medium">{formatUptime(agent.metrics.uptime)}</span>
              </div>
              <Progress 
                value={agent.metrics.uptime} 
                className="h-2"
              />
            </div>

            {/* Last Seen */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Last seen</span>
              <span className="font-medium">
                {formatDistanceToNow(agent.lastSeen, { addSuffix: true })}
              </span>
            </div>

            {/* Agent Endpoint */}
            <div className="space-y-2">
              <div className="text-sm text-muted-foreground">Endpoint</div>
              <div className="flex items-center gap-2">
                <code className="text-xs bg-muted px-2 py-1 rounded flex-1 truncate">
                  {agent.endpoint}
                </code>
                <Button size="sm" variant="ghost" className="h-6 w-6 p-0">
                  <ExternalLink className="h-3 w-3" />
                </Button>
              </div>
            </div>

            {/* Quick Actions */}
            {selectedAgent === agent.id && (
              <div className="flex gap-2 pt-2 border-t">
                <Button size="sm" variant="outline" className="flex-1">
                  View Logs
                </Button>
                <Button size="sm" variant="outline" className="flex-1">
                  Restart
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}