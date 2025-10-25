"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Search, 
  Filter, 
  Eye, 
  Download, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Calendar,
  Database,
  MoreHorizontal,
  RefreshCw
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { QueryResult, ResearchQueryService } from '@/lib/research-query-api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface QueryHistoryProps {
  onViewQuery?: (queryId: string) => void;
  onViewResults?: (queryId: string) => void;
  refreshTrigger?: number;
}

export function QueryHistory({ onViewQuery, onViewResults, refreshTrigger }: QueryHistoryProps) {
  const [queries, setQueries] = useState<QueryResult[]>([]);
  const [filteredQueries, setFilteredQueries] = useState<QueryResult[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  const loadQueries = async () => {
    setIsLoading(true);
    try {
      const researcher = ResearchQueryService.getCurrentResearcher();
      const results = ResearchQueryService.getQueryResults(researcher.researcherId);
      
      // Sort by submission date (newest first)
      const sortedResults = results.sort((a, b) => 
        new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime()
      );
      
      setQueries(sortedResults);
      setFilteredQueries(sortedResults);
    } catch (error) {
      console.error('Failed to load queries:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQueries();
  }, [refreshTrigger]);

  // Filter queries based on search term and status
  useEffect(() => {
    let filtered = queries;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(query =>
        query.studyTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
        query.queryId.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(query => query.status === statusFilter);
    }

    setFilteredQueries(filtered);
  }, [queries, searchTerm, statusFilter]);

  const getStatusIcon = (status: QueryResult['status']) => {
    switch (status) {
      case 'submitted':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'validating':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'processing':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
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

  const getStatusColor = (status: QueryResult['status']) => {
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

  const getStatusCounts = () => {
    return {
      all: queries.length,
      submitted: queries.filter(q => q.status === 'submitted').length,
      validating: queries.filter(q => q.status === 'validating').length,
      processing: queries.filter(q => q.status === 'processing').length,
      completed: queries.filter(q => q.status === 'completed').length,
      failed: queries.filter(q => q.status === 'failed').length,
      cancelled: queries.filter(q => q.status === 'cancelled').length,
    };
  };

  const statusCounts = getStatusCounts();

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading query history...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Queries</p>
                <p className="text-2xl font-bold">{statusCounts.all}</p>
              </div>
              <Database className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold text-green-600">{statusCounts.completed}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Processing</p>
                <p className="text-2xl font-bold text-blue-600">
                  {statusCounts.processing + statusCounts.validating + statusCounts.submitted}
                </p>
              </div>
              <RefreshCw className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Failed</p>
                <p className="text-2xl font-bold text-red-600">{statusCounts.failed}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Query History
          </CardTitle>
          <CardDescription>
            View and manage your research query submissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by study title or query ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status ({statusCounts.all})</SelectItem>
                <SelectItem value="submitted">Submitted ({statusCounts.submitted})</SelectItem>
                <SelectItem value="validating">Validating ({statusCounts.validating})</SelectItem>
                <SelectItem value="processing">Processing ({statusCounts.processing})</SelectItem>
                <SelectItem value="completed">Completed ({statusCounts.completed})</SelectItem>
                <SelectItem value="failed">Failed ({statusCounts.failed})</SelectItem>
                <SelectItem value="cancelled">Cancelled ({statusCounts.cancelled})</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={loadQueries}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          {/* Query Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Study Title</TableHead>
                  <TableHead>Query ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead>Records</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredQueries.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      <div className="flex flex-col items-center gap-2">
                        <Database className="h-8 w-8 text-muted-foreground" />
                        <p className="text-muted-foreground">
                          {searchTerm || statusFilter !== 'all' 
                            ? 'No queries match your filters' 
                            : 'No queries submitted yet'
                          }
                        </p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredQueries.map((query) => (
                    <TableRow key={query.queryId}>
                      <TableCell className="font-medium">
                        <div className="max-w-xs truncate" title={query.studyTitle}>
                          {query.studyTitle}
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-xs bg-muted px-2 py-1 rounded">
                          {query.queryId}
                        </code>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(query.status)}>
                          <div className="flex items-center gap-1">
                            {getStatusIcon(query.status)}
                            {query.status.toUpperCase()}
                          </div>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {format(query.submittedAt, 'MMM dd, yyyy')}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatDistanceToNow(query.submittedAt, { addSuffix: true })}
                        </div>
                      </TableCell>
                      <TableCell>
                        {query.status === 'completed' && query.datasetSummary ? (
                          <div className="text-sm">
                            {query.datasetSummary.totalRecords.toLocaleString()}
                          </div>
                        ) : (
                          <div className="text-sm text-muted-foreground">-</div>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => onViewQuery?.(query.queryId)}>
                              <Eye className="h-4 w-4 mr-2" />
                              View Status
                            </DropdownMenuItem>
                            {query.status === 'completed' && (
                              <>
                                <DropdownMenuItem onClick={() => onViewResults?.(query.queryId)}>
                                  <Database className="h-4 w-4 mr-2" />
                                  View Results
                                </DropdownMenuItem>
                                {query.downloadUrl && (
                                  <DropdownMenuItem asChild>
                                    <a href={query.downloadUrl} download>
                                      <Download className="h-4 w-4 mr-2" />
                                      Download Dataset
                                    </a>
                                  </DropdownMenuItem>
                                )}
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}