'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AgentStatusGrid } from '@/components/monitor/agent-status-grid';
import { MessageFlowDiagram } from '@/components/monitor/message-flow-diagram';
import { PerformanceMetrics } from '@/components/monitor/performance-metrics';
import { LogViewer } from '@/components/monitor/log-viewer';
import { WorkflowTracker } from '@/components/monitor/workflow-tracker';
import { useAgentMonitor } from '@/hooks/use-agent-monitor';
import { AlertTriangle, Activity, MessageSquare, BarChart3, FileText, GitBranch } from 'lucide-react';

export default function MonitorPage() {
  const {
    agents,
    messages,
    metrics,
    logs,
    workflows,
    isConnected,
    reconnect,
    searchLogs,
    filterMessages
  } = useAgentMonitor();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const activeAgents = agents.filter(agent => agent.status === 'active').length;
  const totalMessages = messages.length;
  const activeWorkflows = workflows.filter(workflow => workflow.status === 'running').length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agent Activity Monitor</h1>
          <p className="text-muted-foreground">
            Real-time monitoring of agent status, communication, and workflows
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isConnected ? "default" : "destructive"}>
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>
          {!isConnected && (
            <Button onClick={reconnect} size="sm">
              Reconnect
            </Button>
          )}
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAgents}/5</div>
            <p className="text-xs text-muted-foreground">
              {activeAgents === 5 ? "All systems operational" : "Some agents offline"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Messages Today</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalMessages}</div>
            <p className="text-xs text-muted-foreground">
              Inter-agent communications
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeWorkflows}</div>
            <p className="text-xs text-muted-foreground">
              Currently processing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round((activeAgents / 5) * 100)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Overall system status
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="agents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="agents">Agent Status</TabsTrigger>
          <TabsTrigger value="communication">Communication</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="workflows">Workflows</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <AgentStatusGrid 
            agents={agents}
            onAgentSelect={setSelectedAgent}
            selectedAgent={selectedAgent}
          />
        </TabsContent>

        <TabsContent value="communication" className="space-y-4">
          <div className="flex gap-4 mb-4">
            <Input
              placeholder="Filter messages..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm"
            />
            <Button 
              onClick={() => filterMessages(searchTerm)}
              variant="outline"
            >
              Filter
            </Button>
          </div>
          <MessageFlowDiagram 
            messages={messages}
            agents={agents}
            selectedAgent={selectedAgent}
          />
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <PerformanceMetrics 
            metrics={metrics}
            agents={agents}
          />
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <LogViewer 
            logs={logs}
            onSearch={searchLogs}
            selectedAgent={selectedAgent}
          />
        </TabsContent>

        <TabsContent value="workflows" className="space-y-4">
          <WorkflowTracker 
            workflows={workflows}
            agents={agents}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}