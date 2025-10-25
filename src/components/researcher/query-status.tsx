"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Download, 
  Eye, 
  RefreshCw,
  Calendar,
  User,
  Database,
  Shield,
  Activity
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { QueryStatus, QueryResult, ResearchQueryService } from '@/lib/research-query-api';

interface QueryStatusTrackerProps {
  queryId: string;
  onViewResults?: (queryId: string) => void;
}

export function QueryStatusTracker({ queryId, onViewResults }: QueryStatusTrackerProps) {
  const [status, setStatus] = useState<QueryStatus | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refreshStatus = async () => {
    setIsRefreshing(true);
    try {
      const newStatus = ResearchQueryService.getQueryStatus(queryId);
      const newResult = ResearchQueryService.getQueryResult(queryId);
      
      setStatus(newStatus);
      setResult(newResult);
    } catch (error) {
      console.error('Failed to refresh status:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    refreshStatus();
    
    // Auto-refresh every 5 seconds for active queries
    const interval = setInterval(() => {
      if (status && ['submitted', 'validating', 'processing'].includes(status.status)) {
        refreshStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [queryId, status?.status]);

  if (!status || !result) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading query status...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusIcon = (status: QueryStatus['status']) => {
    switch (status) {
      case 'submitted':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'validating':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'processing':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status: QueryStatus['status']) => {
    switch (status) {
      case 'submitted':
        return 'bg-blue-100 text-blue-800';
      case 'validating':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTimeRemaining = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="space-y-6">
      {/* Query Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(status.status)}
                {result.studyTitle}
              </CardTitle>
              <CardDescription>Query ID: {queryId}</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={getStatusColor(status.status)}>
                {status.status.toUpperCase()}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={refreshStatus}
                disabled={isRefreshing}
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>{status.currentStep}</span>
              <span>{status.progress}%</span>
            </div>
            <Progress value={status.progress} className="w-full" />
            {status.estimatedTimeRemaining && (
              <p className="text-sm text-muted-foreground">
                Estimated time remaining: {formatTimeRemaining(status.estimatedTimeRemaining)}
              </p>
            )}
          </div>

          {/* Error Message */}
          {status.errorMessage && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{status.errorMessage}</AlertDescription>
            </Alert>
          )}

          {/* Query Details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Researcher</p>
                <p className="text-sm text-muted-foreground">{result.researcherId}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Submitted</p>
                <p className="text-sm text-muted-foreground">
                  {formatDistanceToNow(result.submittedAt, { addSuffix: true })}
                </p>
              </div>
            </div>
            {result.completedAt && (
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Completed</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDistanceToNow(result.completedAt, { addSuffix: true })}
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Dataset Summary (if completed) */}
      {status.status === 'completed' && result.datasetSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Dataset Summary
            </CardTitle>
            <CardDescription>
              Overview of the anonymized dataset prepared for your research
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-muted rounded-lg">
                <p className="text-2xl font-bold text-primary">
                  {result.datasetSummary.totalRecords.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">Total Records</p>
              </div>
              <div className="text-center p-4 bg-muted rounded-lg">
                <p className="text-2xl font-bold text-primary">
                  {result.datasetSummary.dataTypes.length}
                </p>
                <p className="text-sm text-muted-foreground">Data Types</p>
              </div>
              <div className="text-center p-4 bg-muted rounded-lg">
                <p className="text-2xl font-bold text-primary">
                  k≥{result.datasetSummary.privacyMetrics.kAnonymity}
                </p>
                <p className="text-sm text-muted-foreground">K-Anonymity</p>
              </div>
              <div className="text-center p-4 bg-muted rounded-lg">
                <p className="text-2xl font-bold text-primary">
                  {(result.datasetSummary.privacyMetrics.suppressionRate * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground">Suppression Rate</p>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <h4 className="font-medium flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Privacy & Anonymization
              </h4>
              <div className="flex flex-wrap gap-2">
                {result.datasetSummary.anonymizationMethods.map((method) => (
                  <Badge key={method} variant="secondary">
                    {method.replace('_', ' ').toUpperCase()}
                  </Badge>
                ))}
              </div>
              <p className="text-sm text-muted-foreground">
                Generalization Level: {result.datasetSummary.privacyMetrics.generalizationLevel}
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">Data Types Included</h4>
              <div className="flex flex-wrap gap-2">
                {result.datasetSummary.dataTypes.map((type) => (
                  <Badge key={type} variant="outline">
                    {type.replace('_', ' ')}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">Date Range</h4>
              <p className="text-sm text-muted-foreground">
                {format(new Date(result.datasetSummary.dateRange.startDate), 'PPP')} - {' '}
                {format(new Date(result.datasetSummary.dateRange.endDate), 'PPP')}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-4">
              <Button onClick={() => onViewResults?.(queryId)} className="flex-1">
                <Eye className="mr-2 h-4 w-4" />
                View Results
              </Button>
              {result.downloadUrl && (
                <Button variant="outline" asChild>
                  <a href={result.downloadUrl} download>
                    <Download className="mr-2 h-4 w-4" />
                    Download Dataset
                  </a>
                </Button>
              )}
            </div>

            {result.expiresAt && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Dataset expires on {format(result.expiresAt, 'PPP')} for privacy compliance.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Processing Log */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Processing Log
          </CardTitle>
          <CardDescription>
            Real-time updates from the agent processing pipeline
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64">
            <div className="space-y-4">
              {result.processingLog.map((log, index) => (
                <div key={index} className="flex gap-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-primary rounded-full mt-2" />
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium">{log.action}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(log.timestamp, 'HH:mm:ss')}
                      </p>
                    </div>
                    <p className="text-sm text-muted-foreground">{log.details}</p>
                    <Badge variant="outline" className="text-xs">
                      {log.agent}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}