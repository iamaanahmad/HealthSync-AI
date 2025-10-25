'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LogEntry } from '@/hooks/use-agent-monitor';
import { FileText, Search, Filter, Download, AlertTriangle, Info, AlertCircle, Bug } from 'lucide-react';
import { format } from 'date-fns';

interface LogViewerProps {
  logs: LogEntry[];
  onSearch: (query: string) => void;
  selectedAgent: string | null;
}

type LogLevel = 'all' | 'info' | 'warn' | 'error' | 'debug';

export function LogViewer({ logs, onSearch, selectedAgent }: LogViewerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<LogLevel>('all');
  const [expandedLog, setExpandedLog] = useState<string | null>(null);

  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      // Filter by selected agent
      if (selectedAgent && log.agentId !== selectedAgent) {
        return false;
      }

      // Filter by log level
      if (levelFilter !== 'all' && log.level !== levelFilter) {
        return false;
      }

      // Filter by search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          log.message.toLowerCase().includes(query) ||
          log.agentId.toLowerCase().includes(query) ||
          (log.context && JSON.stringify(log.context).toLowerCase().includes(query))
        );
      }

      return true;
    });
  }, [logs, selectedAgent, levelFilter, searchQuery]);

  const logLevelCounts = useMemo(() => {
    const counts = { info: 0, warn: 0, error: 0, debug: 0 };
    filteredLogs.forEach(log => {
      counts[log.level]++;
    });
    return counts;
  }, [filteredLogs]);

  const getLevelIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'warn':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'debug':
        return <Bug className="h-4 w-4 text-gray-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'info':
        return 'default';
      case 'warn':
        return 'outline';
      case 'error':
        return 'destructive';
      case 'debug':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  const handleSearch = () => {
    onSearch(searchQuery);
  };

  const exportLogs = () => {
    const logData = filteredLogs.map(log => ({
      timestamp: format(log.timestamp, 'yyyy-MM-dd HH:mm:ss'),
      level: log.level,
      agent: log.agentId,
      message: log.message,
      context: log.context
    }));

    const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-logs-${format(new Date(), 'yyyy-MM-dd-HH-mm-ss')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Log Viewer
          </CardTitle>
          <CardDescription>
            Search and filter agent logs in real-time
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search and Filter Controls */}
          <div className="flex flex-wrap gap-4">
            <div className="flex gap-2 flex-1 min-w-[300px]">
              <Input
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button onClick={handleSearch} size="icon" variant="outline">
                <Search className="h-4 w-4" />
              </Button>
            </div>

            <Select value={levelFilter} onValueChange={(value) => setLevelFilter(value as LogLevel)}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="warn">Warning</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="debug">Debug</SelectItem>
              </SelectContent>
            </Select>

            <Button onClick={exportLogs} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>

          {/* Log Level Summary */}
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-blue-500" />
              <span className="text-sm">Info: {logLevelCounts.info}</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <span className="text-sm">Warn: {logLevelCounts.warn}</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <span className="text-sm">Error: {logLevelCounts.error}</span>
            </div>
            <div className="flex items-center gap-2">
              <Bug className="h-4 w-4 text-gray-500" />
              <span className="text-sm">Debug: {logLevelCounts.debug}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Log Entries */}
      <Card>
        <CardHeader>
          <CardTitle>
            Log Entries ({filteredLogs.length})
          </CardTitle>
          <CardDescription>
            {selectedAgent 
              ? `Showing logs for ${selectedAgent}`
              : 'Showing logs from all agents'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px]">
            <div className="space-y-2">
              {filteredLogs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2" />
                  <div>No logs found</div>
                  <div className="text-sm">Try adjusting your search criteria</div>
                </div>
              ) : (
                filteredLogs.map((log) => (
                  <div
                    key={log.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors hover:bg-muted/50 ${
                      expandedLog === log.id ? 'bg-muted' : ''
                    }`}
                    onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1">
                        {getLevelIcon(log.level)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant={getLevelColor(log.level) as any} className="text-xs">
                              {log.level.toUpperCase()}
                            </Badge>
                            <span className="text-sm font-medium">{log.agentId}</span>
                          </div>
                          <div className="text-sm text-foreground break-words">
                            {log.message}
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground whitespace-nowrap">
                        {format(log.timestamp, 'HH:mm:ss.SSS')}
                      </div>
                    </div>

                    {expandedLog === log.id && log.context && (
                      <div className="mt-3 pt-3 border-t">
                        <div className="text-xs text-muted-foreground mb-2">Context:</div>
                        <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                          {JSON.stringify(log.context, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}