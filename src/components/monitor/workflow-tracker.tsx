'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Agent, Workflow, WorkflowStep } from '@/hooks/use-agent-monitor';
import { GitBranch, Play, Pause, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import { format, formatDistanceToNow, differenceInMilliseconds } from 'date-fns';

interface WorkflowTrackerProps {
  workflows: Workflow[];
  agents: Agent[];
}

export function WorkflowTracker({ workflows, agents }: WorkflowTrackerProps) {
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);

  // Generate mock workflows if none exist
  const mockWorkflows: Workflow[] = useMemo(() => {
    if (workflows.length > 0) return workflows;

    return [
      {
        id: 'wf-consent-update-001',
        name: 'Patient Consent Update',
        status: 'completed',
        startTime: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        endTime: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
        currentStep: 4,
        steps: [
          {
            id: 'step-1',
            name: 'Receive Consent Request',
            agentId: 'patient-consent',
            status: 'completed',
            startTime: new Date(Date.now() - 5 * 60 * 1000),
            endTime: new Date(Date.now() - 4.5 * 60 * 1000),
            result: { consent_type: 'research_data', status: 'granted' }
          },
          {
            id: 'step-2',
            name: 'Validate Consent Data',
            agentId: 'patient-consent',
            status: 'completed',
            startTime: new Date(Date.now() - 4.5 * 60 * 1000),
            endTime: new Date(Date.now() - 4 * 60 * 1000),
            result: { validation: 'passed' }
          },
          {
            id: 'step-3',
            name: 'Update MeTTa Knowledge Graph',
            agentId: 'metta-integration',
            status: 'completed',
            startTime: new Date(Date.now() - 4 * 60 * 1000),
            endTime: new Date(Date.now() - 3 * 60 * 1000),
            result: { graph_updated: true, consent_id: 'consent-123' }
          },
          {
            id: 'step-4',
            name: 'Notify Data Custodian',
            agentId: 'data-custodian',
            status: 'completed',
            startTime: new Date(Date.now() - 3 * 60 * 1000),
            endTime: new Date(Date.now() - 2 * 60 * 1000),
            result: { notification_sent: true }
          }
        ]
      },
      {
        id: 'wf-research-query-002',
        name: 'Research Data Query',
        status: 'running',
        startTime: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
        currentStep: 2,
        steps: [
          {
            id: 'step-1',
            name: 'Validate Research Query',
            agentId: 'research-query',
            status: 'completed',
            startTime: new Date(Date.now() - 2 * 60 * 1000),
            endTime: new Date(Date.now() - 1.5 * 60 * 1000),
            result: { query_valid: true, ethics_approved: true }
          },
          {
            id: 'step-2',
            name: 'Check Patient Consent',
            agentId: 'patient-consent',
            status: 'running',
            startTime: new Date(Date.now() - 1.5 * 60 * 1000)
          },
          {
            id: 'step-3',
            name: 'Retrieve Data',
            agentId: 'data-custodian',
            status: 'pending'
          },
          {
            id: 'step-4',
            name: 'Anonymize Data',
            agentId: 'privacy',
            status: 'pending'
          },
          {
            id: 'step-5',
            name: 'Return Results',
            agentId: 'research-query',
            status: 'pending'
          }
        ]
      },
      {
        id: 'wf-privacy-audit-003',
        name: 'Privacy Compliance Audit',
        status: 'failed',
        startTime: new Date(Date.now() - 10 * 60 * 1000), // 10 minutes ago
        endTime: new Date(Date.now() - 8 * 60 * 1000), // 8 minutes ago
        currentStep: 2,
        steps: [
          {
            id: 'step-1',
            name: 'Initiate Audit',
            agentId: 'privacy',
            status: 'completed',
            startTime: new Date(Date.now() - 10 * 60 * 1000),
            endTime: new Date(Date.now() - 9.5 * 60 * 1000),
            result: { audit_id: 'audit-456' }
          },
          {
            id: 'step-2',
            name: 'Query MeTTa for Privacy Rules',
            agentId: 'metta-integration',
            status: 'failed',
            startTime: new Date(Date.now() - 9.5 * 60 * 1000),
            endTime: new Date(Date.now() - 8 * 60 * 1000),
            result: { error: 'Connection timeout to MeTTa service' }
          }
        ]
      }
    ];
  }, [workflows]);

  const getStatusIcon = (status: Workflow['status'] | WorkflowStep['status']) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: Workflow['status'] | WorkflowStep['status']) => {
    switch (status) {
      case 'running':
        return 'default';
      case 'completed':
        return 'default';
      case 'failed':
        return 'destructive';
      case 'paused':
        return 'outline';
      case 'pending':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  const calculateProgress = (workflow: Workflow): number => {
    const completedSteps = workflow.steps.filter(step => step.status === 'completed').length;
    return (completedSteps / workflow.steps.length) * 100;
  };

  const calculateDuration = (workflow: Workflow): string => {
    if (workflow.endTime) {
      const duration = differenceInMilliseconds(workflow.endTime, workflow.startTime);
      return `${Math.round(duration / 1000)}s`;
    } else {
      const duration = differenceInMilliseconds(new Date(), workflow.startTime);
      return `${Math.round(duration / 1000)}s (ongoing)`;
    }
  };

  const getAgentName = (agentId: string): string => {
    return agents.find(agent => agent.id === agentId)?.name || agentId;
  };

  const workflowStats = useMemo(() => {
    const stats = {
      total: mockWorkflows.length,
      running: mockWorkflows.filter(w => w.status === 'running').length,
      completed: mockWorkflows.filter(w => w.status === 'completed').length,
      failed: mockWorkflows.filter(w => w.status === 'failed').length
    };
    return stats;
  }, [mockWorkflows]);

  return (
    <div className="space-y-6">
      {/* Workflow Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Workflows</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{workflowStats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{workflowStats.running}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{workflowStats.completed}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{workflowStats.failed}</div>
          </CardContent>
        </Card>
      </div>

      {/* Workflow List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workflow Cards */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                Active Workflows
              </CardTitle>
              <CardDescription>
                Currently running and recent workflows
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-3">
                  {mockWorkflows.map((workflow) => (
                    <div
                      key={workflow.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors hover:bg-muted/50 ${
                        selectedWorkflow === workflow.id ? 'bg-muted border-primary' : ''
                      }`}
                      onClick={() => setSelectedWorkflow(
                        selectedWorkflow === workflow.id ? null : workflow.id
                      )}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(workflow.status)}
                          <span className="font-medium">{workflow.name}</span>
                        </div>
                        <Badge variant={getStatusColor(workflow.status) as any}>
                          {workflow.status}
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm text-muted-foreground">
                          <span>Progress</span>
                          <span>{Math.round(calculateProgress(workflow))}%</span>
                        </div>
                        <Progress value={calculateProgress(workflow)} className="h-2" />
                      </div>

                      <div className="flex justify-between text-sm text-muted-foreground mt-3">
                        <span>Started {formatDistanceToNow(workflow.startTime, { addSuffix: true })}</span>
                        <span>Duration: {calculateDuration(workflow)}</span>
                      </div>

                      <div className="text-xs text-muted-foreground mt-2">
                        Step {workflow.currentStep} of {workflow.steps.length}: {
                          workflow.steps[workflow.currentStep - 1]?.name || 'Completed'
                        }
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Workflow Details */}
        <div>
          {selectedWorkflow ? (
            <Card>
              <CardHeader>
                <CardTitle>Workflow Details</CardTitle>
                <CardDescription>
                  Step-by-step execution progress
                </CardDescription>
              </CardHeader>
              <CardContent>
                {(() => {
                  const workflow = mockWorkflows.find(w => w.id === selectedWorkflow);
                  if (!workflow) return null;

                  return (
                    <div className="space-y-4">
                      {/* Workflow Header */}
                      <div className="pb-4 border-b">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold">{workflow.name}</h3>
                          <Badge variant={getStatusColor(workflow.status) as any}>
                            {workflow.status}
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          ID: {workflow.id}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Started: {format(workflow.startTime, 'MMM dd, yyyy HH:mm:ss')}
                        </div>
                        {workflow.endTime && (
                          <div className="text-sm text-muted-foreground">
                            Ended: {format(workflow.endTime, 'MMM dd, yyyy HH:mm:ss')}
                          </div>
                        )}
                      </div>

                      {/* Workflow Steps */}
                      <ScrollArea className="h-[400px]">
                        <div className="space-y-3">
                          {workflow.steps.map((step, index) => (
                            <div key={step.id} className="flex gap-4">
                              {/* Step Number and Status */}
                              <div className="flex flex-col items-center">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                                  step.status === 'completed' ? 'bg-green-100 text-green-700' :
                                  step.status === 'running' ? 'bg-blue-100 text-blue-700' :
                                  step.status === 'failed' ? 'bg-red-100 text-red-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {index + 1}
                                </div>
                                {index < workflow.steps.length - 1 && (
                                  <div className="w-px h-8 bg-border mt-2" />
                                )}
                              </div>

                              {/* Step Details */}
                              <div className="flex-1 pb-4">
                                <div className="flex items-center gap-2 mb-1">
                                  {getStatusIcon(step.status)}
                                  <span className="font-medium">{step.name}</span>
                                </div>
                                
                                <div className="text-sm text-muted-foreground mb-2">
                                  Agent: {getAgentName(step.agentId)}
                                </div>

                                {step.startTime && (
                                  <div className="text-xs text-muted-foreground">
                                    Started: {format(step.startTime, 'HH:mm:ss')}
                                    {step.endTime && (
                                      <span> • Completed: {format(step.endTime, 'HH:mm:ss')}</span>
                                    )}
                                  </div>
                                )}

                                {step.result && (
                                  <div className="mt-2">
                                    <div className="text-xs text-muted-foreground mb-1">Result:</div>
                                    <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                                      {JSON.stringify(step.result, null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  );
                })()}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-[500px]">
                <div className="text-center text-muted-foreground">
                  <GitBranch className="h-8 w-8 mx-auto mb-2" />
                  <div>Select a workflow to view details</div>
                  <div className="text-sm">Click on any workflow to see step-by-step progress</div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}