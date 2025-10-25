"use client";

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Download, 
  Filter, 
  Search, 
  Eye, 
  BarChart3, 
  Database, 
  Shield, 
  FileText, 
  Share2,
  Calendar,
  Users,
  Activity,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  ExternalLink,
  Copy,
  RefreshCw
} from 'lucide-react';
import { format } from 'date-fns';
import { QueryResult, ResearchQueryService } from '@/lib/research-query-api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from '@/components/ui/use-toast';

interface ResultsViewerProps {
  queryId: string;
}

interface DatasetRecord {
  recordId: string;
  patientHash: string;
  ageGroup: string;
  gender: string;
  diagnosis: string;
  treatmentCategory: string;
  outcome: string;
  studyArm?: string;
  followupDays?: number;
  [key: string]: any;
}

export function ResultsViewer({ queryId }: ResultsViewerProps) {
  const [result, setResult] = useState<QueryResult | null>(null);
  const [dataset, setDataset] = useState<DatasetRecord[]>([]);
  const [filteredDataset, setFilteredDataset] = useState<DatasetRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterColumn, setFilterColumn] = useState<string>('all');
  const [filterValue, setFilterValue] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRecords, setSelectedRecords] = useState<Set<string>>(new Set());

  // Load query result and generate mock dataset
  useEffect(() => {
    const loadResult = async () => {
      setIsLoading(true);
      try {
        const queryResult = ResearchQueryService.getQueryResult(queryId);
        if (queryResult && queryResult.status === 'completed') {
          setResult(queryResult);
          
          // Generate mock anonymized dataset
          const mockDataset = generateMockDataset(queryResult);
          setDataset(mockDataset);
          setFilteredDataset(mockDataset);
        }
      } catch (error) {
        console.error('Failed to load results:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadResult();
  }, [queryId]);

  // Filter dataset based on search and filters
  useEffect(() => {
    let filtered = dataset;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(record =>
        Object.values(record).some(value =>
          value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }

    // Apply column filter
    if (filterColumn !== 'all' && filterValue !== 'all') {
      filtered = filtered.filter(record => record[filterColumn] === filterValue);
    }

    setFilteredDataset(filtered);
    setCurrentPage(1);
  }, [dataset, searchTerm, filterColumn, filterValue]);

  // Pagination
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredDataset.slice(startIndex, startIndex + pageSize);
  }, [filteredDataset, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredDataset.length / pageSize);

  // Get unique values for filter dropdown
  const getUniqueValues = (column: string) => {
    return Array.from(new Set(dataset.map(record => record[column]))).filter(Boolean);
  };

  // Generate summary statistics
  const summaryStats = useMemo(() => {
    if (!dataset.length) return null;

    const genderCounts = dataset.reduce((acc, record) => {
      acc[record.gender] = (acc[record.gender] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const ageGroups = dataset.reduce((acc, record) => {
      acc[record.ageGroup] = (acc[record.ageGroup] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const outcomes = dataset.reduce((acc, record) => {
      acc[record.outcome] = (acc[record.outcome] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      totalRecords: dataset.length,
      genderDistribution: genderCounts,
      ageDistribution: ageGroups,
      outcomeDistribution: outcomes,
    };
  }, [dataset]);

  const handleExportData = (format: 'csv' | 'json' | 'xlsx') => {
    const selectedData = selectedRecords.size > 0 
      ? dataset.filter(record => selectedRecords.has(record.recordId))
      : filteredDataset;

    // Mock export functionality
    const blob = new Blob([JSON.stringify(selectedData, null, 2)], { 
      type: format === 'json' ? 'application/json' : 'text/csv' 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research-results-${queryId}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Export Complete",
      description: `Dataset exported as ${format.toUpperCase()} format.`,
    });
  };

  const handleShareResults = () => {
    const shareUrl = `${window.location.origin}/researcher/results/${queryId}`;
    navigator.clipboard.writeText(shareUrl);
    
    toast({
      title: "Share Link Copied",
      description: "Results sharing link copied to clipboard.",
    });
  };

  const toggleRecordSelection = (recordId: string) => {
    const newSelection = new Set(selectedRecords);
    if (newSelection.has(recordId)) {
      newSelection.delete(recordId);
    } else {
      newSelection.add(recordId);
    }
    setSelectedRecords(newSelection);
  };

  const selectAllRecords = () => {
    if (selectedRecords.size === paginatedData.length) {
      setSelectedRecords(new Set());
    } else {
      setSelectedRecords(new Set(paginatedData.map(record => record.recordId)));
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading research results...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result || result.status !== 'completed') {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Results are not available. The query may still be processing or may have failed.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Results Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Research Results
              </CardTitle>
              <CardDescription>
                {result.studyTitle} • Query ID: {queryId}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                <CheckCircle className="h-3 w-3 mr-1" />
                Completed
              </Badge>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Share2 className="h-4 w-4 mr-2" />
                    Share
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleShareResults}>
                    <Copy className="h-4 w-4 mr-2" />
                    Copy Share Link
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Generate Report
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleExportData('csv')}>
                    <FileText className="h-4 w-4 mr-2" />
                    Export as CSV
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleExportData('json')}>
                    <Database className="h-4 w-4 mr-2" />
                    Export as JSON
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleExportData('xlsx')}>
                    <FileText className="h-4 w-4 mr-2" />
                    Export as Excel
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem disabled={selectedRecords.size === 0}>
                    <Eye className="h-4 w-4 mr-2" />
                    Export Selected ({selectedRecords.size})
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Total Records</p>
                <p className="text-2xl font-bold text-primary">
                  {result.datasetSummary.totalRecords.toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Completed</p>
                <p className="text-sm text-muted-foreground">
                  {result.completedAt ? format(result.completedAt, 'MMM dd, yyyy') : 'N/A'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Privacy Level</p>
                <p className="text-sm text-muted-foreground">
                  k≥{result.datasetSummary.privacyMetrics.kAnonymity}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Data Quality</p>
                <p className="text-sm text-muted-foreground">
                  {((1 - result.datasetSummary.privacyMetrics.suppressionRate) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="dataset" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="dataset" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Dataset Viewer
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="collaboration" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Collaboration
          </TabsTrigger>
        </TabsList>

        {/* Dataset Viewer Tab */}
        <TabsContent value="dataset" className="space-y-6">
          {/* Filters and Search */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Dataset Filters</CardTitle>
              <CardDescription>
                Filter and search through the anonymized research dataset
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4 mb-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search across all fields..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <Select value={filterColumn} onValueChange={setFilterColumn}>
                  <SelectTrigger className="w-full sm:w-48">
                    <Filter className="h-4 w-4 mr-2" />
                    <SelectValue placeholder="Filter by column" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Columns</SelectItem>
                    <SelectItem value="gender">Gender</SelectItem>
                    <SelectItem value="ageGroup">Age Group</SelectItem>
                    <SelectItem value="diagnosis">Diagnosis</SelectItem>
                    <SelectItem value="outcome">Outcome</SelectItem>
                  </SelectContent>
                </Select>
                {filterColumn !== 'all' && (
                  <Select value={filterValue} onValueChange={setFilterValue}>
                    <SelectTrigger className="w-full sm:w-48">
                      <SelectValue placeholder="Select value" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Values</SelectItem>
                      {getUniqueValues(filterColumn).map((value) => (
                        <SelectItem key={value} value={value}>
                          {value}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>
                  Showing {paginatedData.length} of {filteredDataset.length} records
                  {selectedRecords.size > 0 && ` (${selectedRecords.size} selected)`}
                </span>
                <Select value={pageSize.toString()} onValueChange={(value) => setPageSize(parseInt(value))}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 per page</SelectItem>
                    <SelectItem value="25">25 per page</SelectItem>
                    <SelectItem value="50">50 per page</SelectItem>
                    <SelectItem value="100">100 per page</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Dataset Table */}
          <Card>
            <CardContent className="p-0">
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">
                        <input
                          type="checkbox"
                          checked={selectedRecords.size === paginatedData.length && paginatedData.length > 0}
                          onChange={selectAllRecords}
                          className="rounded"
                        />
                      </TableHead>
                      <TableHead>Patient Hash</TableHead>
                      <TableHead>Age Group</TableHead>
                      <TableHead>Gender</TableHead>
                      <TableHead>Diagnosis</TableHead>
                      <TableHead>Treatment</TableHead>
                      <TableHead>Outcome</TableHead>
                      <TableHead>Follow-up (Days)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedData.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8">
                          <div className="flex flex-col items-center gap-2">
                            <Database className="h-8 w-8 text-muted-foreground" />
                            <p className="text-muted-foreground">
                              {searchTerm || filterValue !== 'all' 
                                ? 'No records match your filters' 
                                : 'No data available'
                              }
                            </p>
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : (
                      paginatedData.map((record) => (
                        <TableRow key={record.recordId}>
                          <TableCell>
                            <input
                              type="checkbox"
                              checked={selectedRecords.has(record.recordId)}
                              onChange={() => toggleRecordSelection(record.recordId)}
                              className="rounded"
                            />
                          </TableCell>
                          <TableCell>
                            <code className="text-xs bg-muted px-2 py-1 rounded">
                              {record.patientHash}
                            </code>
                          </TableCell>
                          <TableCell>{record.ageGroup}</TableCell>
                          <TableCell>{record.gender}</TableCell>
                          <TableCell>{record.diagnosis}</TableCell>
                          <TableCell>{record.treatmentCategory}</TableCell>
                          <TableCell>
                            <Badge variant={record.outcome === 'Improved' ? 'default' : 'secondary'}>
                              {record.outcome}
                            </Badge>
                          </TableCell>
                          <TableCell>{record.followupDays || 'N/A'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-6 py-4">
                  <div className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          {summaryStats && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Dataset Summary Statistics</CardTitle>
                  <CardDescription>
                    Overview of key demographic and outcome distributions
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Gender Distribution */}
                    <div>
                      <h4 className="font-medium mb-3">Gender Distribution</h4>
                      <div className="space-y-2">
                        {Object.entries(summaryStats.genderDistribution).map(([gender, count]) => (
                          <div key={gender} className="flex items-center justify-between">
                            <span className="text-sm">{gender}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-20 bg-muted rounded-full h-2">
                                <div 
                                  className="bg-primary h-2 rounded-full" 
                                  style={{ width: `${(count / summaryStats.totalRecords) * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium">{count}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Age Distribution */}
                    <div>
                      <h4 className="font-medium mb-3">Age Distribution</h4>
                      <div className="space-y-2">
                        {Object.entries(summaryStats.ageDistribution).map(([age, count]) => (
                          <div key={age} className="flex items-center justify-between">
                            <span className="text-sm">{age}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-20 bg-muted rounded-full h-2">
                                <div 
                                  className="bg-blue-500 h-2 rounded-full" 
                                  style={{ width: `${(count / summaryStats.totalRecords) * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium">{count}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Outcome Distribution */}
                    <div>
                      <h4 className="font-medium mb-3">Outcome Distribution</h4>
                      <div className="space-y-2">
                        {Object.entries(summaryStats.outcomeDistribution).map(([outcome, count]) => (
                          <div key={outcome} className="flex items-center justify-between">
                            <span className="text-sm">{outcome}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-20 bg-muted rounded-full h-2">
                                <div 
                                  className="bg-green-500 h-2 rounded-full" 
                                  style={{ width: `${(count / summaryStats.totalRecords) * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium">{count}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Privacy Compliance Metrics</CardTitle>
                  <CardDescription>
                    Anonymization and privacy protection measures applied to the dataset
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium">K-Anonymity Level</span>
                          <span className="text-sm">k≥{result.datasetSummary.privacyMetrics.kAnonymity}</span>
                        </div>
                        <Progress value={Math.min(100, (result.datasetSummary.privacyMetrics.kAnonymity / 10) * 100)} />
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium">Data Retention</span>
                          <span className="text-sm">
                            {((1 - result.datasetSummary.privacyMetrics.suppressionRate) * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={(1 - result.datasetSummary.privacyMetrics.suppressionRate) * 100} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h4 className="font-medium">Applied Methods</h4>
                      <div className="flex flex-wrap gap-2">
                        {result.datasetSummary.anonymizationMethods.map((method) => (
                          <Badge key={method} variant="outline">
                            {method.replace('_', ' ').toUpperCase()}
                          </Badge>
                        ))}
                      </div>
                      <p className="text-sm text-muted-foreground mt-2">
                        Generalization Level: {result.datasetSummary.privacyMetrics.generalizationLevel}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Collaboration Tab */}
        <TabsContent value="collaboration" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Research Impact & Collaboration</CardTitle>
              <CardDescription>
                Track research impact and collaborate with other researchers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Alert>
                <Activity className="h-4 w-4" />
                <AlertDescription>
                  Collaboration features are currently in development. This will include research impact tracking,
                  citation management, and collaborative analysis tools.
                </AlertDescription>
              </Alert>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Research Impact</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Dataset Downloads</span>
                      <span className="text-sm font-medium">0</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Shared Links</span>
                      <span className="text-sm font-medium">0</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Collaboration Requests</span>
                      <span className="text-sm font-medium">0</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-3">Sharing Options</h4>
                  <div className="space-y-2">
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Share2 className="h-4 w-4 mr-2" />
                      Generate Public Link
                    </Button>
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Users className="h-4 w-4 mr-2" />
                      Invite Collaborators
                    </Button>
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <FileText className="h-4 w-4 mr-2" />
                      Create Research Report
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Helper function to generate mock anonymized dataset
function generateMockDataset(result: QueryResult): DatasetRecord[] {
  const records: DatasetRecord[] = [];
  const totalRecords = result.datasetSummary.totalRecords;

  const genders = ['Male', 'Female', 'Other'];
  const ageGroups = ['18-30', '31-45', '46-60', '61-75', '76+'];
  const diagnoses = [
    'Hypertension', 'Diabetes Type 2', 'Coronary Artery Disease', 
    'Asthma', 'Depression', 'Arthritis', 'Chronic Kidney Disease'
  ];
  const treatments = [
    'Medication Management', 'Lifestyle Intervention', 'Surgical Procedure',
    'Physical Therapy', 'Behavioral Therapy', 'Combination Therapy'
  ];
  const outcomes = ['Improved', 'Stable', 'Declined', 'No Change'];

  for (let i = 0; i < totalRecords; i++) {
    records.push({
      recordId: `REC-${String(i + 1).padStart(6, '0')}`,
      patientHash: `P${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
      ageGroup: ageGroups[Math.floor(Math.random() * ageGroups.length)],
      gender: genders[Math.floor(Math.random() * genders.length)],
      diagnosis: diagnoses[Math.floor(Math.random() * diagnoses.length)],
      treatmentCategory: treatments[Math.floor(Math.random() * treatments.length)],
      outcome: outcomes[Math.floor(Math.random() * outcomes.length)],
      followupDays: Math.random() > 0.3 ? Math.floor(Math.random() * 365) + 30 : undefined,
    });
  }

  return records;
}