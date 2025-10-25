"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { 
  GitBranch, 
  ArrowRight, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
  Zap,
  Clock,
  Target
} from "lucide-react";
import { MeTTaResponse, mettaAPI } from "@/lib/metta-api";

interface ReasoningPathDisplayProps {
  queryResponse: MeTTaResponse | null;
  onStepSelected: (step: string) => void;
}

interface ReasoningStep {
  id: string;
  content: string;
  type: 'info' | 'success' | 'error' | 'warning' | 'process';
  timestamp?: string;
  confidence?: number;
  metadata?: Record<string, any>;
}

interface VisualizationNode {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
}

interface VisualizationEdge {
  source: string;
  target: string;
  label: string;
}

export function ReasoningPathDisplay({ queryResponse, onStepSelected }: ReasoningPathDisplayProps) {
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [visualization, setVisualization] = useState<{
    nodes: VisualizationNode[];
    edges: VisualizationEdge[];
  } | null>(null);

  const parseReasoningSteps = (reasoningPath: string[]): ReasoningStep[] => {
    return reasoningPath.map((step, index) => {
      let type: ReasoningStep['type'] = 'info';
      let confidence: number | undefined;

      // Determine step type based on content
      if (step.toLowerCase().includes('error') || step.toLowerCase().includes('failed')) {
        type = 'error';
      } else if (step.toLowerCase().includes('found') || step.toLowerCase().includes('valid') || step.toLowerCase().includes('approved')) {
        type = 'success';
      } else if (step.toLowerCase().includes('checking') || step.toLowerCase().includes('processing')) {
        type = 'process';
      } else if (step.toLowerCase().includes('warning') || step.toLowerCase().includes('expired')) {
        type = 'warning';
      }

      // Extract confidence if mentioned
      const confidenceMatch = step.match(/confidence[:\s]+(\d+(?:\.\d+)?)/i);
      if (confidenceMatch) {
        confidence = parseFloat(confidenceMatch[1]);
      }

      return {
        id: `step_${index}`,
        content: step,
        type,
        timestamp: new Date(Date.now() + index * 100).toISOString(),
        confidence,
        metadata: {
          index,
          originalText: step
        }
      };
    });
  };

  const getStepIcon = (type: ReasoningStep['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'process':
        return <Zap className="h-4 w-4 text-blue-500" />;
      default:
        return <ArrowRight className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStepColor = (type: ReasoningStep['type']) => {
    switch (type) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'process':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-border bg-background';
    }
  };

  const startAnimation = () => {
    if (!queryResponse?.reasoning_path.length) return;
    
    setIsAnimating(true);
    setCurrentStepIndex(0);
    
    const steps = queryResponse.reasoning_path;
    let index = 0;
    
    const interval = setInterval(() => {
      if (index >= steps.length) {
        setIsAnimating(false);
        clearInterval(interval);
        return;
      }
      
      setCurrentStepIndex(index);
      index++;
    }, 800);
  };

  const resetAnimation = () => {
    setIsAnimating(false);
    setCurrentStepIndex(0);
  };

  const loadVisualization = async () => {
    if (!queryResponse?.query_id) return;
    
    try {
      const vizData = await mettaAPI.getReasoningVisualization(queryResponse.query_id);
      setVisualization(vizData);
    } catch (error) {
      console.error('Failed to load reasoning visualization:', error);
    }
  };

  const handleStepClick = (step: ReasoningStep) => {
    setSelectedStep(step.id);
    onStepSelected(step.content);
  };

  useEffect(() => {
    if (queryResponse) {
      resetAnimation();
      loadVisualization();
    }
  }, [queryResponse]);

  if (!queryResponse) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <GitBranch className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No Reasoning Path</h3>
          <p className="text-muted-foreground">
            Execute a query to see the step-by-step reasoning process
          </p>
        </CardContent>
      </Card>
    );
  }

  const steps = parseReasoningSteps(queryResponse.reasoning_path);
  const overallConfidence = queryResponse.confidence_score;

  return (
    <div className="space-y-6">
      {/* Reasoning Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              Reasoning Overview
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={startAnimation}
                disabled={isAnimating}
              >
                {isAnimating ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {isAnimating ? 'Animating' : 'Animate'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={resetAnimation}
              >
                <RotateCcw className="h-4 w-4" />
                Reset
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{steps.length}</div>
              <div className="text-sm text-muted-foreground">Reasoning Steps</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {(overallConfidence * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">Confidence</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {steps.filter(s => s.type === 'success').length}
              </div>
              <div className="text-sm text-muted-foreground">Successful Steps</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {queryResponse.results.length}
              </div>
              <div className="text-sm text-muted-foreground">Results Found</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Overall Confidence</span>
              <span>{(overallConfidence * 100).toFixed(1)}%</span>
            </div>
            <Progress value={overallConfidence * 100} className="h-2" />
          </div>

          {isAnimating && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Animation Progress</span>
                <span>{currentStepIndex + 1} / {steps.length}</span>
              </div>
              <Progress value={((currentStepIndex + 1) / steps.length) * 100} className="h-2" />
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reasoning Steps */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Reasoning Steps
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-3">
                  {steps.map((step, index) => {
                    const isVisible = !isAnimating || index <= currentStepIndex;
                    const isActive = isAnimating && index === currentStepIndex;
                    const isSelected = selectedStep === step.id;
                    
                    return (
                      <div
                        key={step.id}
                        className={`p-4 rounded-lg border cursor-pointer transition-all duration-300 ${
                          !isVisible 
                            ? 'opacity-30 scale-95' 
                            : isActive 
                              ? 'ring-2 ring-primary shadow-md scale-105' 
                              : isSelected
                                ? 'ring-1 ring-primary'
                                : ''
                        } ${getStepColor(step.type)}`}
                        onClick={() => handleStepClick(step)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 mt-0.5">
                            {getStepIcon(step.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium">Step {index + 1}</span>
                              {step.confidence !== undefined && (
                                <Badge variant="outline" className="text-xs">
                                  {(step.confidence * 100).toFixed(0)}%
                                </Badge>
                              )}
                              <Badge variant="outline" className="text-xs capitalize">
                                {step.type}
                              </Badge>
                            </div>
                            <p className="text-sm text-foreground">{step.content}</p>
                            {step.timestamp && (
                              <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                {new Date(step.timestamp).toLocaleTimeString()}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Step Details & Visualization */}
        <div className="space-y-4">
          {/* Selected Step Details */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Step Details</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedStep ? (
                (() => {
                  const step = steps.find(s => s.id === selectedStep);
                  if (!step) return <div>Step not found</div>;
                  
                  return (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        {getStepIcon(step.type)}
                        <span className="font-medium">Step {step.metadata?.index + 1}</span>
                      </div>
                      
                      <Separator />
                      
                      <div>
                        <div className="text-sm font-medium mb-1">Content</div>
                        <p className="text-sm text-muted-foreground">{step.content}</p>
                      </div>
                      
                      <div>
                        <div className="text-sm font-medium mb-1">Type</div>
                        <Badge variant="outline" className="capitalize">
                          {step.type}
                        </Badge>
                      </div>
                      
                      {step.confidence !== undefined && (
                        <div>
                          <div className="text-sm font-medium mb-1">Confidence</div>
                          <div className="flex items-center gap-2">
                            <Progress value={step.confidence * 100} className="flex-1 h-2" />
                            <span className="text-sm">{(step.confidence * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      )}
                      
                      {step.timestamp && (
                        <div>
                          <div className="text-sm font-medium mb-1">Timestamp</div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(step.timestamp).toLocaleString()}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })()
              ) : (
                <div className="text-center py-6 text-muted-foreground text-sm">
                  Select a reasoning step to view details
                </div>
              )}
            </CardContent>
          </Card>

          {/* Reasoning Flow Visualization */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Reasoning Flow</CardTitle>
            </CardHeader>
            <CardContent>
              {visualization ? (
                <div className="space-y-3">
                  <div className="text-sm font-medium">Process Flow</div>
                  <div className="space-y-2">
                    {visualization.nodes.map((node, index) => (
                      <div key={node.id} className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${
                          node.type === 'start' ? 'bg-green-500' :
                          node.type === 'end' ? 'bg-red-500' :
                          'bg-blue-500'
                        }`} />
                        <span className="text-sm">{node.label}</span>
                        {index < visualization.nodes.length - 1 && (
                          <ArrowRight className="h-3 w-3 text-muted-foreground ml-auto" />
                        )}
                      </div>
                    ))}
                  </div>
                  
                  {visualization.edges.length > 0 && (
                    <>
                      <Separator />
                      <div className="text-sm font-medium">Relationships</div>
                      <div className="space-y-1">
                        {visualization.edges.map((edge, index) => (
                          <div key={index} className="text-xs text-muted-foreground">
                            {edge.source} → {edge.target} ({edge.label})
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground text-sm">
                  Loading reasoning visualization...
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}