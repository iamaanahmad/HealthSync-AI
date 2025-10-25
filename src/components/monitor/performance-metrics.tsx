'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Agent, PerformanceMetric } from '@/hooks/use-agent-monitor';
import { BarChart3, TrendingUp, TrendingDown, AlertTriangle, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { format, subHours, isAfter } from 'date-fns';

interface PerformanceMetricsProps {
  metrics: PerformanceMetric[];
  agents: Agent[];
}

type TimeRange = '1h' | '6h' | '24h' | '7d';
type MetricType = 'response_time' | 'throughput' | 'error_rate' | 'memory_usage' | 'cpu_usage';

export function PerformanceMetrics({ metrics, agents }: PerformanceMetricsProps) {
  const [selectedAgent, setSelectedAgent] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<TimeRange>('1h');
  const [metricType, setMetricType] = useState<MetricType>('response_time');

  // Generate mock performance data since we don't have real metrics yet
  const generateMockMetrics = (agentId: string, hours: number): PerformanceMetric[] => {
    const mockMetrics: PerformanceMetric[] = [];
    const now = new Date();
    
    for (let i = hours; i >= 0; i--) {
      const timestamp = subHours(now, i);
      
      // Response time metrics
      mockMetrics.push({
        timestamp,
        agentId,
        metric: 'response_time',
        value: 100 + Math.random() * 200 + Math.sin(i / 10) * 50,
        unit: 'ms'
      });

      // Throughput metrics
      mockMetrics.push({
        timestamp,
        agentId,
        metric: 'throughput',
        value: 10 + Math.random() * 20 + Math.cos(i / 8) * 5,
        unit: 'req/min'
      });

      // Error rate metrics
      mockMetrics.push({
        timestamp,
        agentId,
        metric: 'error_rate',
        value: Math.random() * 0.05 + (Math.sin(i / 15) + 1) * 0.01,
        unit: '%'
      });

      // Memory usage metrics
      mockMetrics.push({
        timestamp,
        agentId,
        metric: 'memory_usage',
        value: 40 + Math.random() * 30 + Math.sin(i / 12) * 10,
        unit: 'MB'
      });

      // CPU usage metrics
      mockMetrics.push({
        timestamp,
        agentId,
        metric: 'cpu_usage',
        value: 20 + Math.random() * 40 + Math.cos(i / 6) * 15,
        unit: '%'
      });
    }
    
    return mockMetrics;
  };

  const getHoursFromRange = (range: TimeRange): number => {
    switch (range) {
      case '1h': return 1;
      case '6h': return 6;
      case '24h': return 24;
      case '7d': return 168;
      default: return 1;
    }
  };

  const filteredMetrics = useMemo(() => {
    const hours = getHoursFromRange(timeRange);
    const cutoff = subHours(new Date(), hours);
    
    // Generate mock data for all agents
    let allMetrics: PerformanceMetric[] = [];
    
    if (selectedAgent === 'all') {
      agents.forEach(agent => {
        allMetrics = [...allMetrics, ...generateMockMetrics(agent.id, hours)];
      });
    } else {
      allMetrics = generateMockMetrics(selectedAgent, hours);
    }
    
    return allMetrics
      .filter(m => isAfter(m.timestamp, cutoff))
      .filter(m => m.metric === metricType)
      .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  }, [agents, selectedAgent, timeRange, metricType]);

  const chartData = useMemo(() => {
    const dataMap = new Map<string, any>();
    
    filteredMetrics.forEach(metric => {
      const timeKey = format(metric.timestamp, timeRange === '1h' ? 'HH:mm' : 'MMM dd HH:mm');
      
      if (!dataMap.has(timeKey)) {
        dataMap.set(timeKey, { time: timeKey });
      }
      
      const data = dataMap.get(timeKey)!;
      if (selectedAgent === 'all') {
        const agentName = agents.find(a => a.id === metric.agentId)?.name || metric.agentId;
        data[agentName] = metric.value;
      } else {
        data.value = metric.value;
      }
    });
    
    return Array.from(dataMap.values());
  }, [filteredMetrics, selectedAgent, agents, timeRange]);

  const currentMetrics = useMemo(() => {
    return agents.map(agent => {
      const latest = filteredMetrics
        .filter(m => m.agentId === agent.id)
        .slice(-1)[0];
      
      return {
        agent,
        value: latest?.value || 0,
        unit: latest?.unit || '',
        trend: Math.random() > 0.5 ? 'up' : 'down',
        change: (Math.random() * 20 - 10).toFixed(1)
      };
    });
  }, [agents, filteredMetrics]);

  const getMetricLabel = (type: MetricType): string => {
    switch (type) {
      case 'response_time': return 'Response Time';
      case 'throughput': return 'Throughput';
      case 'error_rate': return 'Error Rate';
      case 'memory_usage': return 'Memory Usage';
      case 'cpu_usage': return 'CPU Usage';
      default: return type;
    }
  };

  const getMetricColor = (type: MetricType): string => {
    switch (type) {
      case 'response_time': return '#3b82f6';
      case 'throughput': return '#10b981';
      case 'error_rate': return '#ef4444';
      case 'memory_usage': return '#f59e0b';
      case 'cpu_usage': return '#8b5cf6';
      default: return '#6b7280';
    }
  };

  const formatValue = (value: number, unit: string): string => {
    if (unit === '%') {
      return `${(value * 100).toFixed(2)}%`;
    }
    return `${value.toFixed(1)} ${unit}`;
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap gap-4">
        <Select value={selectedAgent} onValueChange={setSelectedAgent}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Select agent" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Agents</SelectItem>
            {agents.map(agent => (
              <SelectItem key={agent.id} value={agent.id}>
                {agent.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={metricType} onValueChange={(value) => setMetricType(value as MetricType)}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Select metric" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="response_time">Response Time</SelectItem>
            <SelectItem value="throughput">Throughput</SelectItem>
            <SelectItem value="error_rate">Error Rate</SelectItem>
            <SelectItem value="memory_usage">Memory Usage</SelectItem>
            <SelectItem value="cpu_usage">CPU Usage</SelectItem>
          </SelectContent>
        </Select>

        <Select value={timeRange} onValueChange={(value) => setTimeRange(value as TimeRange)}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Time range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1h">1 Hour</SelectItem>
            <SelectItem value="6h">6 Hours</SelectItem>
            <SelectItem value="24h">24 Hours</SelectItem>
            <SelectItem value="7d">7 Days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Current Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {currentMetrics.map(({ agent, value, unit, trend, change }) => (
          <Card key={agent.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">{agent.name}</CardTitle>
              <CardDescription className="text-xs">{getMetricLabel(metricType)}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold">
                  {formatValue(value, unit)}
                </div>
                <div className={`flex items-center gap-1 text-sm ${
                  trend === 'up' ? 'text-red-500' : 'text-green-500'
                }`}>
                  {trend === 'up' ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  {change}%
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            {getMetricLabel(metricType)} Over Time
          </CardTitle>
          <CardDescription>
            {selectedAgent === 'all' 
              ? `${getMetricLabel(metricType)} for all agents over the last ${timeRange}`
              : `${getMetricLabel(metricType)} for ${agents.find(a => a.id === selectedAgent)?.name} over the last ${timeRange}`
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              {selectedAgent === 'all' ? (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  {agents.map((agent, index) => (
                    <Line
                      key={agent.id}
                      type="monotone"
                      dataKey={agent.name}
                      stroke={getMetricColor(metricType)}
                      strokeOpacity={0.8 - (index * 0.1)}
                      strokeWidth={2}
                    />
                  ))}
                </LineChart>
              ) : (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke={getMetricColor(metricType)}
                    strokeWidth={2}
                  />
                </LineChart>
              )}
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Alerts and Thresholds */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Performance Alerts
          </CardTitle>
          <CardDescription>
            Active alerts and threshold violations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {currentMetrics
              .filter(m => {
                // Mock alert conditions
                if (metricType === 'response_time' && m.value > 300) return true;
                if (metricType === 'error_rate' && m.value > 0.03) return true;
                if (metricType === 'memory_usage' && m.value > 80) return true;
                if (metricType === 'cpu_usage' && m.value > 80) return true;
                return false;
              })
              .map(({ agent, value, unit }) => (
                <div key={agent.id} className="flex items-center justify-between p-3 border rounded-lg bg-red-50 border-red-200">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                    <div>
                      <div className="font-medium">{agent.name}</div>
                      <div className="text-sm text-muted-foreground">
                        High {getMetricLabel(metricType).toLowerCase()}
                      </div>
                    </div>
                  </div>
                  <Badge variant="destructive">
                    {formatValue(value, unit)}
                  </Badge>
                </div>
              ))}
            
            {currentMetrics.filter(m => {
              if (metricType === 'response_time' && m.value > 300) return true;
              if (metricType === 'error_rate' && m.value > 0.03) return true;
              if (metricType === 'memory_usage' && m.value > 80) return true;
              if (metricType === 'cpu_usage' && m.value > 80) return true;
              return false;
            }).length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-8 w-8 mx-auto mb-2" />
                <div>No active alerts</div>
                <div className="text-sm">All systems operating within normal parameters</div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}